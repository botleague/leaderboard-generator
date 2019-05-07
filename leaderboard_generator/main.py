from datetime import datetime
import json
import time
import logging as log

import requests

import leaderboard_generator.botleague_gcp.constants as gcp_constants
from leaderboard_generator.botleague_gcp import key_value_store
from leaderboard_generator.generate_html import update_problem_leaderboards
from leaderboard_generator.git_util import GitUtil
import leaderboard_generator.constants as c

log.basicConfig(level=log.INFO)

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


def main(kv=None):
    kv = kv or key_value_store.get_key_value_store()
    while True:
        # Check for should gen trigger
        should_gen = kv.get(gcp_constants.SHOULD_GEN_KEY)
        if should_gen:
            gists = check_for_new_results()
            if gists:
                update_problem_leaderboards(gists)
                # Commit leaderboard/ to github on successful generation
                git_util = GitUtil()
                git_util.commit_and_push_leaderboard()

        #  - Push out to Google Cloud Storage static site on success
        #  - Set should_gen to false
        #  - Poll dead man's snitch every so often
        #  - To auto-deploy python changes, setup GCR build from GitHub and restart instance
        time.sleep(1)


def check_for_new_results():
    with open(c.LAST_GEN_FILEPATH) as last_gen_file:
        last_gen_str = json.load(last_gen_file)['last_gen_time']
        gen_time = datetime.strptime(last_gen_str, '%Y-%m-%dT%H:%M:%SZ')
        search_url = c.GIST_SEARCH.format(time=last_gen_str)
        log.info('Checking gist for new results at %s', search_url)
        gists = None
        while not gists:
            res = requests.get(search_url)
            if res.status_code == 200:
                gists = res.json()
            else:
                log.info('Could not get gist, will retry in a 10 seconds')
                time.sleep(10)

        return gists


if __name__ == '__main__':
    main()

