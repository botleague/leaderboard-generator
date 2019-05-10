import json
import os

import requests


from leaderboard_generator.generate_html import PROBLEM_DATA_DIR
from leaderboard_generator.tally import tally_bot_scores
from leaderboard_generator import logs

log = logs.get_log(__name__)


def update_problem_leaderboards(gists):
    """
    Integrate new gists into our current leaderboard data.
    Note: We only keep the top score from each bot in the problem leaderboards
    """
    problem_map = get_problem_map(gists)

    # For each problem, integrate results into leaderboard
    for problem_name, results in problem_map.items():

        # Each problem has one JSON file
        problem_filename = '%s/%s.json' % (PROBLEM_DATA_DIR, problem_name)

        # Incorporate new scores into existing ones
        if exists_and_unempty(problem_filename):
            with open(problem_filename) as file:
                old_results = json.load(file)['bots']
                results += old_results

        results = tally_bot_scores(results)

        # Write new results
        with open(problem_filename, 'w') as file:
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


def exists_and_unempty(problem_filename):
    return p.exists(problem_filename) and os.stat(problem_filename).st_size != 0