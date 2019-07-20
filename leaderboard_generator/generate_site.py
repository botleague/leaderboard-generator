from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import os
import urllib
from glob import glob
import json
import time
from urllib.parse import urlparse

import grip
from future.builtins import (dict)

import os.path as p
import shutil

from jinja2 import Environment, PackageLoader, select_autoescape
from leaderboard_generator.config import config
from leaderboard_generator import logs

from leaderboard_generator.models.problem import Problem
from leaderboard_generator.util import read_json, exists_and_unempty, read_file, \
    write_file

log = logs.get_log(__name__)

APP = 'leaderboard'
DIR = p.dirname(p.realpath(__file__))
APP_DIR = p.join(DIR, APP)


class SiteGenerator:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader('leaderboard_generator.leaderboard',
                                 'templates'),
            autoescape=select_autoescape(['html', 'xml']))

    def regenerate(self):
        log.info('Regenerating site')

        # Remove the old generated files and replace with static/
        self.create_clean_gen_dir()

        self.regenerate_problem_pages()

        # TODO: Other pages
        #   Users
        #   Challenges
        #   Bots

        log.info('********** Generated new leaderboard **********')

    def regenerate_problem_pages(self):
        """Write all problem leaderboards"""

        log.info('Regenerating problem pages')

        # TODO: Create a problem home page design in problems/index.html

        # Get our Jinja template
        template = self.env.get_template('problem_leaderboard.html')

        # Generate leaderboard for each problem
        problem_results = glob(config.problem_dir + '/*/*/' +
                               Problem.RESULTS_FILENAME)
        for filename in problem_results:
            log.info('Regenerating HTML from: %s', filename)
            results = read_json(filename)
            if not results:
                log.error('No results found in %s', filename)
            else:
                problem_id = results['bots'][0]['problem']
                problem = Problem(problem_id)
                fetched = problem.fetch()
                if fetched:
                    self.write_problem_page(problem, results, template)
                    log.info('Regenerated %s page', problem.id)
                else:
                    log.error('Skipping problem page generation for %s',
                              problem_id)

    @staticmethod
    def write_problem_page(problem, results, template):
        out_filename = p.join(config.problem_html_dir, problem.id + '.html')
        submissions = results['bots']
        add_youtube_embed(submissions)
        if blconfig.is_test:
            readme = 'Skipped readme gen in test, record it to avoid 403s.'
        else:
            readme = ''
            tries = 0
            while not readme and tries < 5:
                try:
                    readme = grip.render_content(problem.readme, render_offline=True)
                except Exception as e:
                    log.error('Grip render call failed, retrying in 10 seconds')
                    time.sleep(10)
                tries += 1
            if not readme:
                log.error('Could not render new readme via github api, '
                          'skipping')
                # TODO: Use offline renderer when it works
                # readme = grip.render_content(problem.readme,
                #                              render_offline=True)
        write_template(out_filename, template, data=dict(
            problem_name=problem.definition['display_name'],
            problem_readme=readme,
            problem_video=get_youtube_embed_url(problem.definition['youtube']),
            submissions=submissions))

    @staticmethod
    def create_clean_gen_dir():
        if p.exists(config.site_dir):
            log.info('Removing %s', config.site_dir)
            shutil.rmtree(config.site_dir)
        log.info('Copying static files to %s', config.site_dir)
        shutil.copytree(p.join(APP_DIR, 'static'), config.site_dir)


def write_template(out_html_filename, template, data):
    write_file(out_html_filename, template.render(data))


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


def generate():
    SiteGenerator().regenerate()


if __name__ == '__main__':
    generate()
