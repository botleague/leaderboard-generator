from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import json
import time

from future.builtins import (dict, input,
                             str)

import os
import os.path as p
import shutil
from distutils.dir_util import copy_tree
from jinja2 import Environment, PackageLoader, select_autoescape


DIR = p.dirname(p.realpath(__file__))
APP = 'leaderboard'
APP_DIR = p.join(DIR, APP)
GEN_DIR = p.join(APP_DIR, 'generated')


def main():
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

        # TODO: Act as if the 2 test/data/ files were just detected
        # on github.

        # TODO: Use the gist time (not the results time) as the official time
        # to avoid weirdness.

        # TODO: The two files should be aggregated into the problem data,
        # where only the top scores are preserved.
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


if __name__ == '__main__':
    main()
