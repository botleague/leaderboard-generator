import json
import os

import requests

from leaderboard_generator.models.problem import Problem
from leaderboard_generator.tally import tally_bot_scores
from leaderboard_generator import logs
from leaderboard_generator.util import exists_and_unempty

log = logs.get_log(__name__)


def update_problem_results(gists):
    """
    Integrate new gists into our current leaderboard data.
    Note: We only keep the top score from each bot in the problem leaderboards
    """
    problem_map = get_problem_map(gists)

    # For each problem, integrate results into leaderboard
    for problem_id, results in problem_map.items():
        problem = Problem(problem_id)

        # Incorporate new scores into existing ones
        if exists_and_unempty(problem.results_filepath):
            with open(problem.results_filepath) as file:
                old_results = json.load(file)['bots']
                results += old_results

        results = tally_bot_scores(results)

        # Write new results
        with open(problem.results_filepath, 'w') as file:
            json.dump({"bots": results}, file, indent=2)


def get_problem_map(gists):
    problem_map = {}
    for gist in gists:
        # Download the gist results
        gist_json = requests.get(url=gist['url']).json()
        result_json = json.loads(
            gist_json['files']['results.json']['content'])
        result_json['gist_time'] = gist['created_at']
        if 'problem' not in result_json:
            log.error('No "problem" in this gist, skipping')
        else:
            # Map results JSON into {problem: [results...]}
            problem_map.setdefault(result_json['problem'], []).append(
                result_json)
    return problem_map


