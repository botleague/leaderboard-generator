from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

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

import leaderboard_generator.constants as c
from leaderboard_generator.botleague_gcp.constants import GITHUB_TOKEN
from leaderboard_generator.util import load_json, write_file, read_file

log = logs.get_log(__name__)


DIR = p.dirname(p.realpath(__file__))
APP = 'leaderboard'
APP_DIR = p.join(DIR, APP)


class HtmlGenerator:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader(APP, 'templates'),
            autoescape=select_autoescape(['html', 'xml']))
        self.last_run = -1
        github.enable_console_debug_logging()
        self.github = Github(GITHUB_TOKEN)
        self.botleague_repo = self.github.get_repo('deepdrive/botleague')

    def regenerate_html(self):
        if self.last_run != -1 and time.time() - self.last_run < 1:
            # Avoid regen loop locally via watchdog
            print('Skipping generation, too soon!')
            return

        # Remove the old generated files and replace with static/
        self.create_clean_gen_dir()

        self.update_problem_leaderboards()

        # TODO: Other pages
        #   Users
        #   Challenges
        #   Bots

        with open(c.LAST_GEN_FILEPATH, 'w') as outtime:
            json.dump(dict(last_gen_time=time.time()), outtime)

        print('\n********** Generated new leaderboard **********\n')

        self.last_run = time.time()

    def update_problem_leaderboards(self):
        """Write all problem leaderboards"""

        # TODO: Create a problem home page design in problems/index.html

        # Get our Jinja template
        template = self.env.get_template('problem_leaderboard.html')

        # Generate leaderboard for each problem
        problem_files = glob(c.LEADERBOARD_DIR + '/data/problems/*.json')
        for filename in problem_files:
            results = load_json(filename)
            if results:
                problem_id = results['bots'][0]['problem']
                problem_def, readme = self.get_problem_def(problem_id)
                out_filename = p.join(c.GEN_DIR, 'problems',
                                      problem_id + '.html')
                submissions = results['bots']
                add_youtube_embed(submissions)
                write_template(out_filename, template, data=dict(
                    problem_name=problem_def['display_name'],
                    problem_readme=readme,
                    problem_video='https://www.youtube.com/embed/ALdsqfrLieg',
                    submissions=submissions))

    def get_problem_def(self, problem_id):
        path = p.join(c.PROBLEM_DEFINITIONS_DIR, problem_id)
        problem_filename = 'problem.json'
        readme_filename = 'README.md'
        problem_path = path + '/' + problem_filename
        readme_path = path + '/' + readme_filename
        if p.exists(path):
            definition = load_json(problem_path)
            readme = read_file(readme_path)
        else:
            # New problem, get definition json from botleague
            # TODO: Don't allow this if submissions have been made by
            #  authors other than creator
            problem_dir = 'problems/%s' % problem_id
            definition_str = self.get_file_from_github(
                problem_dir + '/' + problem_filename)
            definition = json.loads(definition_str)
            readme = self.get_file_from_github(
                problem_dir + '/' + readme_filename)
            write_file(definition_str, problem_path)
            write_file(readme, readme_path)

        return definition, readme

    def get_file_from_github(self, path):
        contents = self.botleague_repo.get_contents(path)
        content_str = contents.decoded_content
        return content_str

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
    HtmlGenerator().regenerate_html()
