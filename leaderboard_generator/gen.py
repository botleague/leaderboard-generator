from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import json
import time

import requests
from future.builtins import (dict, input,
                             str)

import os
import os.path as p
import shutil
from distutils.dir_util import copy_tree
from jinja2 import Environment, PackageLoader, select_autoescape

import logging as log
log.basicConfig(level=log.INFO)


DIR = p.dirname(p.realpath(__file__))
PROBLEM_DIR = p.join(DIR, 'leaderboard', 'data', 'problems')
APP = 'leaderboard'
APP_DIR = p.join(DIR, APP)
GEN_DIR = p.join(APP_DIR, 'generated')


def regenerate_html():
    last_gen_filename = p.join(GEN_DIR, 'last-generation-time.json')
    if p.exists(last_gen_filename):
        with open(last_gen_filename) as last_gen_file:
            last_gen = json.load(last_gen_file)['last_gen_time']
            if time.time() - last_gen < 1:
                print('Skipping generation, too soon!')
                return

    env = Environment(
        loader=PackageLoader(APP, 'templates'),
        autoescape=select_autoescape(['html', 'xml']))

    # TODO:
    #  - Trigger on PR to agent_zoo
    #  - Test this with forward-agent
    #  - Go through results.json files on gist stored since last
    #    date stamp stored in generated/data/last-result-time.json
    #  - If new artifacts in api request, https://api.github.com/users/deepdrive-results/gists?since=2019-04-03T23:31:31Z then regen
    #  - Keep some raw and processed data
    #       data/users.json
    #       data/agents.json
    #       data/problem/problem_name.json
    #       data/results
    #  - Problems will reference a sim binary / container.
    #  - Challenges will be collections of problems.
    #  - Fuzzing of the problem will be part of the implementation.
    #    - Fuzzing requires some rethinking of how recording and visualization happens

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


def get_best_result_for_bot(results):

    # Keep older bots if tie
    results.sort(key=lambda x: x['utc_timestamp'])

    ret = {}
    url_prefix = 'https://github.com/'
    for result in results:
        url = result['agent_source_commit']
        if not url.startswith(url_prefix):
            log.error('Skipping submission with github url in incorrect '
                      'format: %s' % url)
        else:
            botname = url[len(url_prefix):].split('/')[1]
            if botname in ret:
                current = ret[botname]
                if current['score'] < result['score']:
                    ret[botname] = result
            else:
                ret[botname] = result

    # Add botname to result
    for r in ret:
        ret[r]['botname'] = r

    ret = list(ret.values())
    ret.sort(key=lambda x: x['score'], reverse=True)
    return ret


def exists_and_unempty(problem_filename):
    return p.exists(problem_filename) and os.stat(problem_filename).st_size != 0


def update_problem_leaderboards(gists):
    """
    Integrate new gists into our current leaderboard data.
    Note: We only keep the top score from each bot in the problem leaderboards
    """
    results = {}
    for gist in gists:
        # Download the gist results
        result_json = requests.get(url=gist['url']).json()
        result_json['gist_time'] = gist['created_at']
        if 'problem' not in result_json:
            log.error('No "problem" in this gist, skipping')
        else:
            # Map results JSON into {problem: [results...]}
            results.setdefault(result_json['problem'], []).append(result_json)

    # For each problem, integrate results into leaderboard
    for problem_name, new_results in results.items():

        # Dedupe new results, in case the same bot has two new scores since
        # the last update
        new_results = get_best_result_for_bot(new_results)

        # Each problem has one JSON file
        problem_filename = '%s/%s.json' % (PROBLEM_DIR, problem_name)

        # Incorporate new scores into existing ones
        if exists_and_unempty(problem_filename):
            with open(problem_filename) as file:
                old_results = json.load(file)['bots']
                new_results = get_best_result_for_bot(new_results + old_results)

        # Sort results by score
        new_results.sort(key=lambda x: x['score'])

        # Write new results
        with open(problem_filename, 'w') as file:
            json.dump({"bots": new_results}, file)

        # regenerate_html()


if __name__ == '__main__':
    regenerate_html()
