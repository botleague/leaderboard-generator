import json


def load_json(filename):
    with open(filename) as file:
        results = json.load(file)
    return results
