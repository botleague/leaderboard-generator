import time
import requests
from github import Github

import leaderboard_generator.constants as c
from leaderboard_generator.key_value_store import get_key_value_store

if c.SHOULD_USE_FIRESTORE:
    import firebase_admin
    firebase_admin.initialize_app()


def main():
    kv = get_key_value_store()
    while True:

        # Check Firestore for should gen trigger
        should_gen = kv.get(c.SHOULD_GEN_KEY)
        if should_gen:
            pass

        # TODO:
        #  - Check for latest leaderboard/ from github on start,
        #  - If Firestore, ask results.json files on gist stored since last
        #    date stamp stored in generated/data/last-generation-time.json
        #  - If new artifacts in api request, https://api.github.com/users/deepdrive-results/gists?since=2019-04-03T23:31:31Z then regen
        #  - Commit leaderboard/ to github on successful generation
        #  - Push out to Google Cloud Storage static site on success
        #  - Poll dead man's snitch every so often
        #  - To auto-deploy python changes, setup GCR build from GitHub and restart instance

        print(requests.get(
            'https://api.github.com/users/deepdrive-results/gists?since=2019-04-02T23:31:31Z'))
        time.sleep(10)


if __name__ == '__main__':
    main()

