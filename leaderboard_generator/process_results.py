import json
import os.path as p

import requests

from leaderboard_generator.models.problem import Problem
from leaderboard_generator.tally import tally_bot_scores
from leaderboard_generator import logs
from leaderboard_generator.util import exists_and_unempty, write_file, \
    read_file, read_json
from leaderboard_generator.config import config

log = logs.get_log(__name__)


def update_problem_results(gists):
    """
    Integrate new gists into our current leaderboard data.
    Note: We only keep the top score from each bot in the problem leaderboards
    """
    problem_map = get_problem_map(gists)
    log.info('Updating problem leaderboards for the following problems %r',
             problem_map.keys())

    # For each problem, integrate results into leaderboard
    for problem_id, results in problem_map.items():
        problem = Problem(problem_id)

        # Incorporate new scores into existing ones
        if exists_and_unempty(problem.results_filepath):
            log.info('Adding new results to existing problem: %s', problem.id)
            old_results_str = read_file(problem.results_filepath)
            old_results = json.loads(old_results_str)['bots']
            results += old_results
        else:
            log.info('Adding new problem: %s', problem.id)

        # Aggregate scores
        results = tally_bot_scores(results)

        # Write new results
        write_file(json.dumps({"bots": results}, indent=2),
                   problem.results_filepath)


def get_problem_map(gists):
    problem_map = {}
    for gist in gists:
        # Download the gist results
        file = gist['files'].get('results.json', '')
        if not file:
            log.error('No "results.json" in gist, skipping %s', gist['url'])
        else:
            if config.should_mock_github:
                result_json = read_json(
                    p.join(config.mock_services_dir, 'gists', gist['id'] + '.json'))
            else:
                url = file['raw_url']
                result_json = requests.get(url).json()
            result_json['gist_time'] = gist['created_at']
            if 'problem' not in result_json:
                log.error('No "problem" in gist, skipping %s', url)
            else:
                # Map results JSON into {problem: [results...]}
                problem_map.setdefault(result_json['problem'], []).append(
                    result_json)
    return problem_map


