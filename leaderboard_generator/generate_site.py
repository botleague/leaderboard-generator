from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import os
import urllib
from glob import glob
import json
import time
from urllib.parse import urlparse

import github
import requests
from future.builtins import (dict)

import os.path as p
import shutil
from distutils.dir_util import copy_tree

from github import Github
from jinja2 import Environment, PackageLoader, select_autoescape
from leaderboard_generator import logs

import leaderboard_generator.config as c
from leaderboard_generator.models.problem import Problem
from leaderboard_generator.util import load_json, write_file, read_file

log = logs.get_log(__name__)


DIR = p.dirname(p.realpath(__file__))
APP = 'leaderboard'
APP_DIR = p.join(DIR, APP)


class SiteGenerator:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader(APP, 'templates'),
            autoescape=select_autoescape(['html', 'xml']))
        self.last_run = -1

    def regenerate(self):
        if self.last_run != -1 and time.time() - self.last_run < 1:
            # Avoid regen loop locally via watchdog
            print('Skipping generation, too soon!')
            return

        # Remove the old generated files and replace with static/
        self.create_clean_gen_dir()

        self.regenerate_problem_pages()

        # TODO: Other pages
        #   Users
        #   Challenges
        #   Bots

        with open(c.LAST_GEN_FILEPATH, 'w') as outtime:
            json.dump(dict(last_gen_time=time.time()), outtime)

        print('\n********** Generated new leaderboard **********\n')

        self.last_run = time.time()

    def regenerate_problem_pages(self):
        """Write all problem leaderboards"""

        # TODO: Create a problem home page design in problems/index.html

        # Get our Jinja template
        template = self.env.get_template('problem_leaderboard.html')

        # Generate leaderboard for each problem
        problem_files = glob(c.LEADERBOARD_DIR + '/data/problems/*/' +
                             Problem.RESULTS_FILENAME)
        for filename in problem_files:
            results = load_json(filename)
            if results:
                problem_id = results['bots'][0]['problem']
                problem = Problem(problem_id).fetch()
                out_filename = p.join(c.GEN_DIR, 'problems',
                                      problem_id + '.html')
                submissions = results['bots']
                add_youtube_embed(submissions)
                write_template(out_filename, template, data=dict(
                    problem_name=problem.definition['display_name'],
                    problem_readme=problem.readme,
                    problem_video='https://www.youtube.com/embed/Q57rzaHHO0k',
                    submissions=submissions))

    @staticmethod
    def create_clean_gen_dir():
        if p.exists(c.GEN_DIR):
            shutil.rmtree(c.GEN_DIR)
        copy_tree(p.join(APP_DIR, 'static'), c.GEN_DIR)


def write_template(out_html_filename, template, data):
    with open(out_html_filename, 'w') as outfile:
        outfile.write(template.render(data))


def add_youtube_embed(submissions):
    for submission in submissions:
        url = submission['youtube']
        submission['youtube_embed'] = get_youtube_embed_url(url)


def get_youtube_embed_url(url):
    parsed = urlparse(url)
    query_dict = urllib.parse.parse_qs(parsed.query)
    if 'v' in query_dict:
        embed_url = '%s://%s/embed/%s' % (parsed.scheme, parsed.netloc,
                                          query_dict['v'][0])
    else:
        embed_url = url
    return embed_url


if __name__ == '__main__':
    SiteGenerator().regenerate()
