from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import json
import time

import requests
from future.builtins import (dict)

import os
import os.path as p
import shutil
from distutils.dir_util import copy_tree
from jinja2 import Environment, PackageLoader, select_autoescape

import logging as log

from leaderboard_generator.tally import tally_bot_scores

log.basicConfig(level=log.INFO)


DIR = p.dirname(p.realpath(__file__))
PROBLEM_DIR = p.join(DIR, 'leaderboard', 'data', 'problems')
APP = 'leaderboard'
APP_DIR = p.join(DIR, APP)
GEN_DIR = p.join(APP_DIR, 'generated')


def regenerate_html(last_gen_time):
    if time.time() - last_gen_time < 1:
        # Avoid regen loop locally via watchdog
        print('Skipping generation, too soon!')
        return

    env = Environment(
        loader=PackageLoader(APP, 'templates'),
        autoescape=select_autoescape(['html', 'xml']))

    page = 'leaderboard.html'
    env.get_template(page)
    template = env.get_template(page)
    if p.exists(GEN_DIR):
        shutil.rmtree(GEN_DIR)
    os.makedirs(GEN_DIR)

    with open(p.join(GEN_DIR, page), 'w') as outfile:
        # After results are returned to ci-hooks with the correct key, they
        # are uploaded to a special gist account that this will be polling.
        outfile.write(template.render(
            problem_name='Unprotected left scenario',
            submissions=[dict(
                user='drewjgray3',
                score='5.6k',
                time='86400000',
                github_url='https://github.com/deepdrive/deepdrive',
                github_name='drewjgray/SuperAgent',
                youtube_url='https://www.youtube.com/embed/Un8_yXtTAps'
            )]
        ),)

    with open(p.join(GEN_DIR, 'last-generation-time.json'), 'w') as outtime:
        json.dump(dict(last_gen_time=time.time()), outtime)

    copy_tree(p.join(APP_DIR, 'static'), GEN_DIR)
    print('\n********** Generated new leaderboard **********\n')


def exists_and_unempty(problem_filename):
    return p.exists(problem_filename) and os.stat(problem_filename).st_size != 0


def update_problem_leaderboards(gists):
    """
    Integrate new gists into our current leaderboard data.
    Note: We only keep the top score from each bot in the problem leaderboards
    """
    problem_map = get_problem_map(gists)

    # For each problem, integrate results into leaderboard
    for problem_name, results in problem_map.items():

        # Each problem has one JSON file
        problem_filename = '%s/%s.json' % (PROBLEM_DIR, problem_name)

        # Incorporate new scores into existing ones
        if exists_and_unempty(problem_filename):
            with open(problem_filename) as file:
                old_results = json.load(file)['bots']
                results += old_results

        results = tally_bot_scores(results)

        # Write new results
        with open(problem_filename, 'w') as file:
            json.dump({"bots": results}, file)


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


if __name__ == '__main__':
    regenerate_html()
