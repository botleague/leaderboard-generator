import os
import os.path as p
from datetime import datetime, timedelta
import json
import time

import requests
from google.cloud import storage

import leaderboard_generator.botleague_gcp.constants as gcp_constants
from leaderboard_generator.auto_git import get_auto_git
from leaderboard_generator.botleague_gcp import key_value_store
from leaderboard_generator.botleague_gcp.key_value_store import \
    get_key_value_store, SimpleKeyValueStore
from leaderboard_generator.generate_site import SiteGenerator
from leaderboard_generator.config import c
from leaderboard_generator import logs, cmd
from leaderboard_generator.process_results import update_problem_results
from leaderboard_generator.util import read_file, read_lines, append_file, \
    write_file, exists_and_unempty, read_json

log = logs.get_log(__name__)


r"""
 ______________________________________________
|                                              |
| Only run one of these processes at a time!   |
| This is designed to run as a single process  |
| event loop. Multiple instances will probably |
| not cause any problems, so long as they're   |
| in different places, but I wouldn't try it.  |
|______________________________________________|
"""
# https://boxes.thomasjensen.com
# boxes -l #  list options
# sudo apt-get install boxes
# cat ../single-warning.txt | boxes -d nuke

GIST_DATE_FMT = '%Y-%m-%dT%H:%M:%SZ'


def get_last_gen_time() -> datetime:
    path = c.last_gist_time_filepath
    if not p.exists(path):
        write_file('2019-05-07T19:47:27Z', path)
    return datetime.strptime(read_file(path), GIST_DATE_FMT)


# TODO: Get liaison pushing results.json/bot readme's on pull request to gist and GCS
# TODO: Get liaison to set should_gen in db when problem readme's are changed on botleague repo.

def main(kv: SimpleKeyValueStore = None, max_iters=-1) -> int:
    try:
        if c.dry_run:
            max_iters = 1
        ret = gen_loop(kv, max_iters)
    finally:
        if c.dry_run:
            git = get_auto_git()
            git.reset_generated_files_hard()
    return ret


def gen_loop(kv: SimpleKeyValueStore = None, max_iters=-1):
    log.info('Starting leaderboard generator')
    kv = kv or key_value_store.get_key_value_store()
    git_util = get_auto_git()
    site_gen = SiteGenerator()
    last_ping_time = -1
    num_iters = 0
    done = False

    # Whether to check gist again, in case the search index was not updated
    # immediately.
    should_retry = False

    log.info('Polling db for new results...')

    while not done:
        start = time.time()

        # Ping cronitor start
        ping_cronitor(start, last_ping_time, 'run')

        # Check for should gen trigger in db
        should_gen = kv.get(gcp_constants.SHOULD_GEN_KEY)

        if should_gen or c.force_gen:
            # Generate!
            should_retry = generate(site_gen, git_util)

        # Commit generated site to github
        git_util.commit_and_push()

        # Sync with Google Cloud Storage where static site is hosted
        gcs_rsync()

        if should_retry:
            log.info('Not setting should_gen to false, will trigger a retry.')
        elif should_gen:
            # Set should gen to false in db
            log.info('Resetting should_gen to false in db')
            kv.set(gcp_constants.SHOULD_GEN_KEY, False)

        # Ping cronitor complete
        last_ping_time = ping_cronitor(start, last_ping_time, 'complete')

        num_iters += 1
        done = num_iters == max_iters

        if not done:
            time.sleep(1)
        else:
            log.info('Max iters of %r reached, terminating' % num_iters)

    return num_iters


def generate(site_gen, should_retry):
    log.info('Should gen is set, checking gist for results')

    # Check for new results posted to gist by liaison since last gen
    last_gen_time = get_last_gen_time()

    # Not adding delta here to avoid race conditions
    search_after_time = last_gen_time + timedelta(seconds=0)

    # Search gist for new results
    gists = check_for_new_results(get_gist_date(search_after_time))

    # Process results or retry
    if gists:
        aggregate_results(gists)
        should_retry = False  # Success, don't retry
    else:
        should_retry = wait_for_gists_index(should_retry)

    # Update HTML with new results
    site_gen.regenerate()

    return should_retry


def get_gist_date(search_after_time):
    return datetime.strftime(search_after_time,
                             GIST_DATE_FMT)


def aggregate_results(gists):
    log.info('%r new result(s) found, updating leaderboards',
             len(gists))

    # Update aggregated results in /data
    update_problem_results(gists)

    # Write last generation time to file
    write_last_gen_time(gists[-1]['created_at'])

    # Store processed gist ids
    store_processed_gist_ids(gists)


def gcs_rsync():
    dry_run_param = '-n' if c.is_test or c.dry_run else ''
    gcs_data_dir = 'data'
    try:

        res1, _ = cmd.run("gsutil -m rsync "  # Multi-threaded rsync
                          "-r "  # Recurse into directories
                          "{dry_run} "  # Just see what would change
                          "-x '{data}/' "  # Ignore data, we will rysnc it after
                          "{gen_dir} "  # Local generated site files
                          "gs://{bucket}"  # Destination on GCS
                          .format(gen_dir=c.gen_dir, data=gcs_data_dir,
                                  bucket=c.gcs_bucket, dry_run=dry_run_param),
                          verbose=False)
        res2, _ = cmd.run("gsutil -m rsync "  # Multi-threaded rsync
                          "-r "  # Recurse into directories
                          "{dry_run} "  # Just see what would change
                          "{data_dir} "  # Local generated data files
                          "gs://{bucket}/data"  # Destination on GCS
                          .format(data_dir=c.data_dir, data=gcs_data_dir,
                                  bucket=c.gcs_bucket, dry_run=dry_run_param),
                          verbose=False)
        res = res1 + '\n' + res2
        if 'Copying ' in res:
            log.info(res)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            'You may need to append something like '
            '/home/your-user/bin/google-cloud-sdk/bin to your '
            'PATH for this to work')


def store_processed_gist_ids(gists):
    gist_ids = [g['id'] for g in gists]
    log.info('Marking gist ids as processed %s', '\n'.join(gist_ids))
    append_file(c.results_gist_ids_filepath, gist_ids)


def write_last_gen_time(time_str):
    path = c.last_gist_time_filepath
    log.info('Writing last generation time to %s', path)
    write_file(time_str, path)


def wait_for_gists_index(should_retry):
    if should_retry:
        # We've already waited and retried, assume spurious
        # should_gen.
        log.error('No new results found on gist, despite should gen '
                  'being set and waiting 10 seconds. Assuming '
                  'should_gen was set in db without there actually '
                  'being new results.')
        should_retry = False
    else:
        # Retry
        log.error('No new results found on gist, despite should gen'
                  ' being set! Trying again in 10 seconds.')
        should_retry = True
        if c.is_test or c.dry_run:
            log.info('Not sleeping in tests or dry runs')
        else:
            time.sleep(10)
    return should_retry


def ping_cronitor(now, ping_time, state):
    if not c.is_test and (ping_time == -1 or now - ping_time > 60):
        log.debug('Pinging cronitor with %s', state)
        # Ping cronitor every minute
        requests.get('https://cronitor.link/mtbC2O/%s' % state, timeout=10)
        return now
    return ping_time


def push_to_gcs(changed_filenames):
    if not changed_filenames:
        log.info('Nothing to push to GCS')
    elif c.should_mock_gcs:
        log.info('Would push the following to GCS, but we are testing:'
                 '\n\t%s', '\n\t'.join(changed_filenames))
    else:
        log.info('Pushing changed site files to gcs')
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(c.gcs_bucket)
        folder = 'leaderboard'
        maybe_backup_manually(bucket, folder)
        for relative_path in changed_filenames:
            path = p.join(c.root_dir, relative_path)

            if path.startswith(c.gen_dir):
                # Make generated directory root of bucket
                blob_name = path[len(c.data_dir) + 1:]
            elif path.startswith(c.data_dir):
                # Put data in data subdirectory
                blob_name = 'data/' + path[len(c.data_dir) + 1:]
            else:
                log.error('Path not in data or site dir, skipping upload of %s',
                          path)
                blob_name = ''

            if blob_name:
                # Upload
                log.info('Uploading %s to botleague.io/%s', path, blob_name)
                bucket.blob(blob_name).upload_from_filename(path)


def maybe_backup_manually(bucket, folder):
    if 'BACKUP_GCP_MANUAL' in os.environ:
        log.warn('Manually backing up bucket')
        # TODO: Backup to different bucket if you resurrect this!!!

        # We use bucket versioning + this is slow + github commits
        backup_old_leaderboard(bucket, folder)


def backup_old_leaderboard(bucket, folder):
    blobs = list(bucket.list_blobs(prefix='leaderboard/'))
    if blobs:
        date_str = datetime.now().strftime('%Y-%m-%d__%I-%M-%S%p')
        new_folder = '%s-%s' % (folder, date_str)
        for blob in blobs:
            postfix = blob.name.replace(folder, '')
            if postfix != '/':
                # Don't rename folder nodes
                bucket.rename_blob(blob, '%s%s' %
                                   (new_folder, postfix))


def check_for_new_results(last_gen_time):
    search_url = c.gist_search_template.format(time=last_gen_time)
    log.info('Checking gist for new results at %s', search_url)
    gists = None
    already_processed_gist_ids = get_processed_gist_ids()
    while not gists:
        gists = search_gist(search_url)

    gists.sort(key=lambda x: x['created_at'])
    ret = [g for g in gists if g['id'] not in already_processed_gist_ids]
    return ret


def search_gist(url) -> dict:
    if c.is_test:
        gists = c.mock_gist_search[url]
    else:
        res = requests.get(url)
        if res.status_code == 200:
            gists = res.json()
        else:
            log.info('Could not get gist, will retry in a 10 seconds')
            time.sleep(10)
            return {}
    return gists


def get_processed_gist_ids() -> set:
    if exists_and_unempty(c.results_gist_ids_filepath):
        ret = set(read_lines(c.results_gist_ids_filepath))
    else:
        ret = set()
    return ret


def run_locally(kv, max_iters):
    assert gcp_constants.SHOULD_USE_FIRESTORE is False
    assert c.should_mock_git and c.should_mock_gcs
    return main(kv, max_iters)


if __name__ == '__main__':
    main()

