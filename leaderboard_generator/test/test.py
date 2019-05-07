import pytest

# pytest ../test

import os.path as p
from leaderboard_generator.botleague_gcp.constants import SHOULD_GEN_KEY
from leaderboard_generator.botleague_gcp.key_value_store import \
    get_key_value_store
from leaderboard_generator.generate_html import update_problem_leaderboards
from leaderboard_generator.main import main
from leaderboard_generator.tally import set_ranks

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


def test_tie_score_different_bot():
    bots = [
        {'score': 10},
        {'score': 10},
        {'score': 0},
        {'score': 0},
        {'score': 0},
        {'score': -1},
        {'score': -1},
    ]
    set_ranks(bots)
    assert bots[0]['rank'] == 1
    assert bots[1]['rank'] == 1
    assert bots[2]['rank'] == 3
    assert bots[3]['rank'] == 3
    assert bots[4]['rank'] == 3
    assert bots[5]['rank'] == 6
    assert bots[6]['rank'] == 6

# TODO: Test tie scores same bot (should keep older one)



def test_main():
    kv = get_key_value_store()
    kv.set(SHOULD_GEN_KEY, True)
    main(kv)


if __name__ == '__main__':
    test_two_files()
