import time
import requests
import os

if os.environ.get('SHOULD_USE_FIRESTORE', 'true') == 'true':
    import firebase_admin
    from firebase_admin import firestore
    firebase_admin.initialize_app()

while True:
    print(requests.get('https://api.github.com/users/deepdrive-results/gists?since=2019-04-02T23:31:31Z'))
    time.sleep(10)