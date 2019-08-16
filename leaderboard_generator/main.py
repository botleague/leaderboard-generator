import os
import os.path as p
import sys
from datetime import datetime, timedelta
import json
import time

import requests
from google.cloud import storage

from botleague_helpers.config import blconfig
from botleague_helpers import key_value_store
from botleague_helpers.key_value_store import SimpleKeyValueStore
from leaderboard_generator.auto_git import get_auto_git
from leaderboard_generator.generate_site import SiteGenerator
from leaderboard_generator.config import config
from leaderboard_generator import logs, cmd
from leaderboard_generator.models.base import Base, \
    clear_cached_botleague_repo_contents
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


def get_last_gist_time() -> datetime:
    if config.regen_no_cache:
        date_str = '2019-08-15T01:42:05Z'
    else:
        path = config.last_gist_time_filepath
        if not p.exists(path):
            write_file(path, '2019-05-07T19:47:27Z')
        date_str = read_file(path)
    return datetime.strptime(date_str, GIST_DATE_FMT)


# TODO: Get liaison to set should_gen in db when problem readme's are changed
#  on botleague repo.

# TODO: Directory structure:
#   /bots - Bots ranked by points
#   --/{github_user_or_org}/{botname} - Bot's submissions ranked points or latest submission
#   --/{github_user_or_org} => redirects to /users/{username}
#   /challenges - Challenge list ranked by latest submission
#   --/{challenge-name} - Challenge home page with, bots ranked by points on challenge
#   /users - Users ranked by points
#   --/{github_user_or_org}  - User's bots ranked points or latest submission
#   /problems/{github_user_or_org} - List of problems ranked by last submission
#   --/problems/{github_user_or_org}/{problem-name} - Problem home page (DONE)

# TODO: liaison scaffolding - pull request to botleague => botleague liaison => GAE problem endpoint API /eval request eval.deepdrive.io => k8s job run => results.json POST back to botleague liaison => and finally post to the botleague-results gist.
# TODO Setup forward agent, MNET2 agent, and path follow agent. Path follow agent will require a special #baseline tag, that allows it to run the in-game AI and not send controls over.
#   Then for us to run CI, we just create pull requests against the botleague repo on commit to the deepdrive repo in a standard CI like Travis.
#   Then I'd poll GitHub for the resolution of the pull request (which kind of sucks), but authenticated users get 5000 requests per hour, so polling once a second should be fine.


def main(kv: SimpleKeyValueStore = None, max_iters=-1, unattended=False) -> int:
    if not unattended and '-y' not in sys.argv:
        input('Press Enter if is the only instance of leaderboard-generator '
              'running')
    try:
        if config.dry_run:
            max_iters = 1
        ret = gen_loop(kv, max_iters)
    finally:
        if config.dry_run:
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
    clear_cached_botleague_repo_contents()

    # Whether to check gist again, in case the search index was not updated
    # immediately.
    should_retry = False

    log.info('Polling db for new results...')

    while not done:
        start = time.time()

        # Ping cronitor start
        ping_cronitor(start, last_ping_time, 'run')

        # Check for should gen trigger in db
        should_gen = kv.get(blconfig.should_gen_key)

        if should_gen or config.force_gen:
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
            kv.set(blconfig.should_gen_key, False)

        # Ping cronitor complete
        last_ping_time = ping_cronitor(start, last_ping_time,
                                                    'complete')

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
    last_gist_time = get_last_gist_time()

    # Not adding delta here to avoid race conditions
    search_after_time = last_gist_time + timedelta(seconds=0)

    # Search gist for new results
    gists = check_for_new_results(get_gist_date(search_after_time))

    # Process results or retry
    if gists:
        aggregate_results(gists)
        # TODO(post launch):
        #  Store all gists in config.gist_dir, so we don't need to refetch
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
    write_last_gist_time(gists[-1]['created_at'])

    # Store processed gist ids
    store_processed_gist_ids(gists)


def gcs_rsync():
    do_dry_run = config.should_mock_gcs or config.dry_run or config.is_test
    dry_run_param = '-n' if do_dry_run else ''
    gcs_data_dir = 'data'
    try:

        res1, _ = cmd.run(
            "gsutil -m rsync "  # Multi-threaded rsync
            "-r "  # Recurse into directories
            "{dry_run} "  # Whether to do a dry run
            "-x '{ignore}/' "  # Don't delete data
            "{site_dir} "  # Local generated site files
            "gs://{bucket}"  # Destination on GCS
            .format(site_dir=config.site_dir, ignore=gcs_data_dir,
                    bucket=config.gcs_bucket, dry_run=dry_run_param),
            verbose=False)
        res2, _ = cmd.run(
            "gsutil -m rsync "  # Multi-threaded rsync
            "-r "  # Recurse into directories
            "{dry_run} "  # Whether to do a dry run
            "{data_dir} "  # Local generated data files
            "gs://{bucket}/data"  # Destination on GCS
            .format(data_dir=config.data_dir, bucket=config.gcs_bucket,
                    dry_run=dry_run_param),
            verbose=False)
        res = res1 + '\n' + res2
        if do_dry_run or 'Copying ' in res:
            log.info(res)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            'You may need to append something like '
            '/home/your-user/bin/google-cloud-sdk/bin to your '
            'PATH for this to work')


def store_processed_gist_ids(gists):
    new_gist_ids = {g['id']: None for g in gists}  # Use a dict to get ordering
    cache_file = config.results_gist_ids_filepath
    log.info('Marking gist ids as processed %s', '\n'.join(new_gist_ids))
    current_gist_ids = {gist_id: None for gist_id in read_lines(cache_file)}
    current_gist_ids.update(new_gist_ids)
    write_file(config.results_gist_ids_filepath,
               '\n'.join(current_gist_ids.keys()) + '\n')


def write_last_gist_time(time_str):
    path = config.last_gist_time_filepath
    log.info('Writing last generation time to %s', path)
    write_file(path, time_str)


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
        if blconfig.is_test or config.dry_run:
            log.info('Not sleeping in tests or dry runs')
        else:
            time.sleep(10)
    return should_retry


def ping_cronitor(now, last_ping_time, state):
    if not blconfig.is_test:
        log.debug('Pinging cronitor with %s', state)
        # Ping cronitor every minute
        requests.get('https://cronitor.link/mtbC2O/%s' % state, timeout=10)
        return now
    return last_ping_time


def push_to_gcs(changed_filenames):
    """DEPRECATED: Use gcs_rsync instead"""
    if not changed_filenames:
        log.info('Nothing to push to GCS')
    elif config.should_mock_gcs:
        log.info('Would push the following to GCS, but we are testing:'
                 '\n\t%s', '\n\t'.join(changed_filenames))
    else:
        log.info('Pushing changed site files to gcs')
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(config.gcs_bucket)
        folder = 'leaderboard'
        maybe_backup_manually(bucket, folder)
        for relative_path in changed_filenames:
            path = p.join(config.root_dir, relative_path)

            if path.startswith(config.site_dir):
                # Make generated directory root of bucket
                blob_name = path[len(config.data_dir) + 1:]
            elif path.startswith(config.data_dir):
                # Put data in data subdirectory
                blob_name = 'data/' + path[len(config.data_dir) + 1:]
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

        # We now use bucket versioning + this is slow + github commits
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


def check_for_new_results(last_gist_time):
    search_url = config.gist_search_template.format(time=last_gist_time)
    log.info('Checking gist for new results at %s', search_url)
    gists = None
    already_processed_gist_ids = get_processed_gist_ids()
    while not gists:
        gists = search_gist(search_url)

    gists.sort(key=lambda x: x['created_at'])

    # We limit returned gists by search time and id's as github will return
    # the latest gist that we set the search time for. We could increment
    # the search time by one second, but that would risk missing results
    # submitted one second after the last time we generated.
    ret = [g for g in gists if g['id'] not in already_processed_gist_ids]
    return ret


def search_gist(url) -> dict:
    if config.should_mock_github:
        gists = config.mock_gist_search[url]
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
    if config.regen_no_cache:
        ret = set()
    elif exists_and_unempty(config.results_gist_ids_filepath):
        ret = set(read_lines(config.results_gist_ids_filepath))
    else:
        ret = set()
    return ret


def run_locally(kv, max_iters, unattended=True):
    assert blconfig.should_use_firestore is False
    assert config.should_mock_git and config.should_mock_gcs
    return main(kv, max_iters, unattended)


if __name__ == '__main__':
    main()

