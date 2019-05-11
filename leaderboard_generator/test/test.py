import pytest

# pytest ../test

import os.path as p
from leaderboard_generator.botleague_gcp.constants import SHOULD_GEN_KEY
from leaderboard_generator.botleague_gcp.key_value_store import \
    get_key_value_store
from leaderboard_generator.main import main
from leaderboard_generator.process_results import update_problem_results
from leaderboard_generator.tally import set_ranks, tally_bot_scores

DIR = p.dirname(p.realpath(__file__))


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



if __name__ == '__main__':
    test_two_files()
