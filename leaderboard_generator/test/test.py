import pytest

# pytest ../test

import os.path as p
import os

# Duplicated in case someone puts stuff in package __init__.py
from leaderboard_generator.auto_git import get_auto_git
from leaderboard_generator.config import IS_TEST
from leaderboard_generator.util import read_json

os.environ['SHOULD_USE_FIRESTORE'] = 'false'
os.environ['SHOULD_MOCK_GIT'] = 'true'
os.environ['SHOULD_MOCK_GCS'] = 'true'
os.environ['IS_TEST'] = 'true'

from leaderboard_generator.botleague_gcp.constants import SHOULD_USE_FIRESTORE

assert IS_TEST
assert SHOULD_USE_FIRESTORE is False

from leaderboard_generator.botleague_gcp.key_value_store import \
    get_key_value_store
from leaderboard_generator import main
from leaderboard_generator.process_results import update_problem_results
from leaderboard_generator.tally import set_ranks, tally_bot_scores
import leaderboard_generator.config as c

DIR = p.dirname(p.realpath(__file__))
MOCK_GIST_SEARCH = read_json(p.join(c.DATA_DIR, 'gists', 'searches.json'))


def test_two_files():
    gists = [
        dict(created_at='2019-04-03T23:29:31Z',
             url='https://gist.githubusercontent.com/crizCraig/982145a5cc6103a3ba35cc6a3b5ea721/raw/1fea7fb385d972162d7ac884c105890057230b9a/results.json'),
        dict(created_at='2019-04-03T23:31:31Z',
             url='https://gist.githubusercontent.com/crizCraig/534fc0629382351565ccc390ede9064e/raw/060caa50c71962ebaa9146948528fbc4d2bed4e2/results.json')
    ]
    update_problem_results(gists)

    # TODO: Asserts!
    pass


def test_new_problem():
    pass


def test_tie_score_ranking():
    results = [
        {'score': 10},
        {'score': 10},
        {'score': 0},
        {'score': 0},
        {'score': 0},
        {'score': -1},
        {'score': -1},
    ]
    set_ranks(results)
    assert results[0]['rank'] == 1
    assert results[1]['rank'] == 1
    assert results[2]['rank'] == 3
    assert results[3]['rank'] == 3
    assert results[4]['rank'] == 3
    assert results[5]['rank'] == 6
    assert results[6]['rank'] == 6


def test_tie_score_same_bot():
    c = 'https://github.com/u1/%s/blah'
    a = 'agent_source_commit'
    u = 'utc_timestamp'
    bots = [
        {a: c % 'point8predict', 'score': 10, u: 1234},
        {a: c % 'point8predict', 'score': 10, u: 1233},
        {a: c % 'point9predict', 'score': 20, u: 1000},
        {a: c % 'point9predict', 'score': 20, u: 1001},
    ]
    bots = tally_bot_scores(bots)
    assert bots[0]['score'] == 20
    assert bots[1]['score'] == 10
    assert bots[0][u] == 1000
    assert bots[1][u] == 1233


def test_main():
    main.run_locally(max_iters=1)

    # TODO: assert a bunch of stuff
    # TODO: Get changed files

    git = get_auto_git()
    changed_files = []
    for path in git.PATHS:
        changed_files += git.get_changed_filenames(path)

    git.reset()


if __name__ == '__main__':
    test_two_files()
