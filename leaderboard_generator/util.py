import json


def load_json(filename):
    with open(filename) as file:
        results = json.load(file)
    return results


def write_file(content, path):
    with open(path, 'w') as f:
        f.write(content)


def read_file(path):
    with open(path) as f:
        ret = f.read()
    return ret
