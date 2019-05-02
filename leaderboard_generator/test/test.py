import pytest

# pytest .

import os.path as p

from glob import glob

from gen import process_new_results

DIR = p.dirname(p.realpath(__file__))


def test_two_files():
    gists = [
        dict(created_at='2019-04-03T23:29:31Z',
             url='https://gist.github.com/crizCraig/982145a5cc6103a3ba35cc6a3b5ea721'),
        dict(created_at='2019-04-03T23:31:31Z',
             url='https://gist.github.com/crizCraig/534fc0629382351565ccc390ede9064e')
    ]


def test_new_problem():
    pass
