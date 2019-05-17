import json
import os
import os.path as p


def read_json(filename):
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


def read_lines(path):
    content = read_file(path)
    lines = content.split()
    return lines


def append_file(path, strings):
    with open(path, 'a') as f:
        f.write('\n'.join(strings) + '\n')


def exists_and_unempty(problem_filename):
    return p.exists(problem_filename) and os.stat(problem_filename).st_size != 0


def is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )