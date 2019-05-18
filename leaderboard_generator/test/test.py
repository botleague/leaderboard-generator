import pytest

# pytest ../test

import os.path as p
import os

# Duplicated in case someone puts stuff in package __init__.py
os.environ['SHOULD_USE_FIRESTORE'] = 'false'
os.environ['SHOULD_MOCK_GIT'] = 'true'
os.environ['SHOULD_MOCK_GCS'] = 'true'
os.environ['IS_TEST'] = 'true'

from leaderboard_generator.auto_git import get_auto_git
from leaderboard_generator.config import c
from leaderboard_generator.models.problem import Problem
from leaderboard_generator.util import read_json, read_file, read_lines, \
    exists_and_unempty

from leaderboard_generator.botleague_gcp.constants \
    import SHOULD_USE_FIRESTORE, SHOULD_GEN_KEY

assert c.is_test
assert SHOULD_USE_FIRESTORE is False

from leaderboard_generator.botleague_gcp.key_value_store import \
    get_key_value_store
from leaderboard_generator import main
from leaderboard_generator.process_results import update_problem_results
from leaderboard_generator.tally import set_ranks, tally_bot_scores
from leaderboard_generator.config import c

DIR = p.dirname(p.realpath(__file__))


def test_two_files_at_once():
    # gists = [
    #     dict(created_at='2019-04-03T23:29:31Z',
    #          url='https://gist.githubusercontent.com/crizCraig/982145a5cc6103a3ba35cc6a3b5ea721/raw/1fea7fb385d972162d7ac884c105890057230b9a/results.json'),
    #     dict(created_at='2019-04-03T23:31:31Z',
    #          url='https://gist.githubusercontent.com/crizCraig/534fc0629382351565ccc390ede9064e/raw/060caa50c71962ebaa9146948528fbc4d2bed4e2/results.json')
    # ]
    # update_problem_results(gists)

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
    prefix = 'https://github.com/u1/%s/blah'
    a = 'agent_source_commit'
    u = 'utc_timestamp'
    bots = [
        {a: prefix % 'point8predict', 'score': 10, u: 1234},
        {a: prefix % 'point8predict', 'score': 10, u: 1233},
        {a: prefix % 'point9predict', 'score': 20, u: 1000},
        {a: prefix % 'point9predict', 'score': 20, u: 1001},
    ]
    bots = tally_bot_scores(bots)
    assert bots[0]['score'] == 20
    assert bots[1]['score'] == 10
    assert bots[0][u] == 1000
    assert bots[1][u] == 1233


def test_main_sanity():
    c.relative_gen_parent = p.join(c.test_dir, 'main_sanity_files')

    # Get a local key value store
    kv = get_key_value_store()
    kv.set(SHOULD_GEN_KEY, True)
    git = get_auto_git()
    git.reset_generated_files_hard()

    try:
        # Run the generation in the test dir
        num_iters = main.run_locally(kv, max_iters=1)

        staged_changes = []
        for path in git.paths:
            staged_changes += git.get_staged_changes(path)

        root = p.dirname(p.dirname(DIR))

        expected_prob_dir = p.join(c.problem_dir, 'domain_randomization')
        expected_def = p.join(expected_prob_dir, 'problem.json')
        expected_readme = p.join(expected_prob_dir, 'README.md')

        # Ensure we fetched and created the new problem files
        assert p.exists(expected_prob_dir)
        assert p.exists(expected_def)
        assert p.exists(expected_readme)

        # Assert problem.json and README.md are in changed files
        assert expected_def[len(root)+1:] in staged_changes
        assert expected_readme[len(root)+1:] in staged_changes

        # Ensure we reset should gen back to false
        assert kv.get(SHOULD_GEN_KEY) is False

        # Test that we looped once
        assert num_iters == 1

        # Ensure last gist time
        last_gist_time = read_file(c.last_gist_time_filepath)
        assert last_gist_time == '2019-05-07T19:47:27Z'

        # Ensure we stored the gist id
        gist_id = read_lines(c.results_gist_ids_filepath)[0]
        assert gist_id == '46e77ca190417540fdf662b2076e5de3'

        # Assert that HTML files were created and are filled
        assert exists_and_unempty(p.join(c.problem_html_dir,
                                         'domain_randomization.html'))
    finally:
        git.reset_generated_files_hard()


if __name__ == '__main__':
    test_two_files_at_once()
