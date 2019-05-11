import os
import os.path as p
from datetime import datetime, timedelta
import json
import time

import requests
from google.cloud import storage

import leaderboard_generator.botleague_gcp.constants as gcp_constants
from leaderboard_generator.botleague_gcp import key_value_store
from leaderboard_generator.generate_site import SiteGenerator
from leaderboard_generator.git_util import GitUtil
import leaderboard_generator.config as c
from leaderboard_generator import logs
from leaderboard_generator.process_results import update_problem_results
from leaderboard_generator.util import read_file, read_lines, append_file

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


def get_last_gen_time():
    with open(c.LAST_GEN_FILEPATH) as last_gen_file:
        gen_str = last_gen_file.read()
        gen_time = datetime.strptime(gen_str, GIST_DATE_FMT)
    return gen_time


def main(kv=None):
    log.info('Starting leaderboard generator')
    kv = kv or key_value_store.get_key_value_store()
    git_util = GitUtil()
    generator = SiteGenerator()
    last_ping_time = -1
    while True:
        start = time.time()

        # Ping cronitor start
        ping_cronitor(start, last_ping_time, 'run')

        # Check for should gen trigger in db
        should_gen = kv.get(gcp_constants.SHOULD_GEN_KEY)

        if should_gen:
            log.info('Should gen is set, checking gist for results')

            # Check for new results posted to gist by liaison since last gen
            last_gen_time = get_last_gen_time()

            # Not adding seconds here to avoid race conditions
            search_after_time = last_gen_time + timedelta(seconds=0)

            gists = check_for_new_results(datetime.strftime(search_after_time,
                                                            GIST_DATE_FMT))

            if gists:
                log.info('%r new results found, updating leaderboards',
                         len(gists))

                update_problem_results(gists)

                # Update HTML with results
                generator.regenerate()

                # Write last generation time to file
                with open(c.LAST_GEN_FILEPATH, 'w') as last_gen_file:
                    gen_time = gists[-1]['created_at']
                    last_gen_file.write(gen_time)

                # Commit leaderboard/ to github
                changed_filenames = git_util.commit_and_push_leaderboard()

                # Push to Google Cloud Storage where static site is hosted
                push_to_gcs(changed_filenames)

                # Store processed gist ids
                gist_ids = [g['id'] for g in gists]
                append_file(c.RESULTS_GIST_IDS_FILEPATH, gist_ids)

        # Set should gen to false in db
        kv.set(gcp_constants.SHOULD_GEN_KEY, False)

        # Ping cronitor complete
        last_ping_time = ping_cronitor(start, last_ping_time, 'complete')

        time.sleep(1)


def ping_cronitor(now, ping_time, state):
    if ping_time == -1 or now - ping_time > 60:
        # Ping cronitor every minute
        requests.get('https://cronitor.link/mtbC2O/%s' % state, timeout=10)
        return now
    return ping_time


def push_to_gcs(changed_filenames):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('botleague.io')
    folder = 'leaderboard'
    maybe_backup_manually(bucket, folder)
    for filename in changed_filenames:
        bucket.blob('leaderboard/%s' % filename). \
            upload_from_filename(p.join(c.ROOT_DIR, filename))


def maybe_backup_manually(bucket, folder):
    if 'BACKUP_GCP_MANUAL' in os.environ:
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
    search_url = c.GIST_SEARCH.format(time=last_gen_time)
    log.info('Checking gist for new results at %s', search_url)
    gists = None
    already_processed_gist_ids = set(read_lines(c.RESULTS_GIST_IDS_FILEPATH))
    while not gists:
        res = requests.get(search_url)
        if res.status_code == 200:
            gists = res.json()
        else:
            log.info('Could not get gist, will retry in a 10 seconds')
            time.sleep(10)

    gists.sort(key=lambda x: x['created_at'])
    ret = [g for g in gists if g['id'] not in already_processed_gist_ids]
    return ret


if __name__ == '__main__':
    main()

