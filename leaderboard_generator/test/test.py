import pytest

# pytest ../test

import os.path as p
from leaderboard_generator.gen import update_problem_leaderboards

DIR = p.dirname(p.realpath(__file__))


def test_two_files():
    gists = [
        dict(created_at='2019-04-03T23:29:31Z',
             url='https://gist.githubusercontent.com/crizCraig/982145a5cc6103a3ba35cc6a3b5ea721/raw/0b2dc9a70cb0b5bff1d4ca9e7591910fe21bed03/results.json'),
        dict(created_at='2019-04-03T23:31:31Z',
             url='https://gist.githubusercontent.com/crizCraig/534fc0629382351565ccc390ede9064e/raw/3ab5e5680948bcf0eb07a3c32551f5157c3a8a59/results.json')
    ]
    update_problem_leaderboards(gists)

    # TODO: Asserts!
    pass


def test_new_problem():
    pass


# TODO: Test tie scores (should keep older one)


if __name__ == '__main__':
    test_two_files()
