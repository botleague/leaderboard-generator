from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import math
import os
import urllib
from glob import glob
import json
import time
from urllib.parse import urlparse

import grip
from botleague_helpers.config import blconfig
from box import Box
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


def add_ride_description(submissions):
    # TODO: If collision, show collision stat in a big box and with vehicle #}
    for s in submissions:
        d = s.driving_specific
        if d.harmful_gforces:
            desc = 'Hazardous'
        elif d.jarring_pct and d.jarring_pct >= 10:
            desc = 'Extremely jarring!'
        elif d.jarring_pct and d.jarring_pct > 0:
            desc = 'Jarring'
        elif d.comfort_pct and d.comfort_pct < 50:
            desc = 'Very uncomfortable'
        elif d.comfort_pct and d.comfort_pct < 80:
            desc = 'Uncomfortable'
        elif d.comfort_pct and d.comfort_pct < 99:
            desc = 'Smooth'
        elif d.comfort_pct and d.comfort_pct < 99:
            desc = 'Perfect!'
        else:
            desc = 'n/a'
        s.ride_description = desc


def add_closest_vehicle_display(submissions):
    for s in submissions:
        dist = s.driving_specific.closest_vehicle_meters
        if not dist or dist == math.inf:
            s.driving_specific.closest_vehicle_meters_display = ''
        else:
            s.driving_specific.closest_vehicle_meters_display = dist


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
        #   Home
        #   Users (post launch)
        #   Challenges (post launch)
        #   Bots (post launch)

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
            results = Box.from_json(filename=filename, default_box=True)
            if not results:
                log.error('No results found in %s', filename)
            else:
                problem_id = results.bots[0].problem
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
        submissions = results.bots
        add_youtube_embed(submissions)
        add_ride_description(submissions)
        add_closest_vehicle_display(submissions)
        if blconfig.is_test:
            readme = 'Skipped readme gen in test, record it to avoid 403s.'
        else:
            readme = ''
            tries = 0
            while not readme and tries < 5:
                try:
                    readme = grip.render_content(problem.readme,
                                                 username='crizcraig',
                                                 password=blconfig.github_token)
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

        problem_video = ''
        if 'youtube' in problem.definition:
            problem_video = get_youtube_embed_url(problem.definition['youtube'])
        write_template(out_filename, template, data=dict(
            # problem_domain=problem.definition['display_name'],
            problem_name=problem.definition['display_name'],
            problem_readme=readme,
            problem_video=problem_video,
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
