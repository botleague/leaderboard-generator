import json
import os
from os.path import basename, exists, isfile, dirname


def read_json(filename):
    with open(filename) as file:
        results = json.load(file)
    return results


def write_file(path, content):
    os.makedirs(dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)


def read_file(path):
    with open(path) as f:
        ret = f.read()
    return ret


def read_lines(path):
    content = read_file(path)
    lines = content.split()
    return lines


def append_file(path, strings):
    with open(path, 'a') as f:
        f.write('\n'.join(strings) + '\n')


def exists_and_unempty(problem_filename):
    return exists(problem_filename) and os.stat(problem_filename).st_size != 0


def is_docker():
    path = '/proc/self/cgroup'
    return (
        exists('/.dockerenv') or
        isfile(path) and any('docker' in line for line in open(path))
    )
