import time
import requests
from github import Github

import leaderboard_generator.constants as c
from leaderboard_generator.key_value_store import get_key_value_store

r"""
                  _ ._  _ , _ ._
                (_ ' ( `  )_  .__)
              ( (  (    )   `)  ) _)
             (__ (_   (_ . _) _) ,__)
                 `~~`\ ' . /`~~`
                 ,::: ;   ; :::,
                ':::::::::::::::'
 ____________________/_ __ \___________________
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


def main():
    kv = get_key_value_store()
    while True:

        # Check Firestore for should gen trigger
        should_gen = kv.get(c.SHOULD_GEN_KEY)
        if should_gen:
            # TODO:
            #  - If Firestore, ask results.json files on gist stored since last
            #    date stamp stored in generated/data/last-generation-time.json
            #  - If new artifacts in api request, https://api.github.com/users/deepdrive-results/gists?since=2019-04-03T23:31:31Z then regen
            print(requests.get(
                'https://api.github.com/users/deepdrive-results/gists?since=2019-04-02T23:31:31Z'))

            # Commit leaderboard/ to github on successful generation
            # github_client = Github(c.GITHUB_TOKEN)
            # repo = github_client


        #  - Commit leaderboard/ to github on successful generation
        #  - Push out to Google Cloud Storage static site on success
        #  - Set should_gen to false
        #  - Poll dead man's snitch every so often
        #  - To auto-deploy python changes, setup GCR build from GitHub and restart instance

        print(requests.get(
            'https://api.github.com/users/deepdrive-results/gists?since=2019-04-02T23:31:31Z'))
        time.sleep(10)


if __name__ == '__main__':
    main()

