import os
import os.path as p

import github

from leaderboard_generator.util import read_json
from leaderboard_generator import logs, util

log = logs.get_log(__name__)


class Config:

    # Constants
    root_dir = p.dirname(p.dirname(p.realpath(__file__)))
    relative_dir = 'leaderboard_generator'
    relative_leaderboard_dir = p.join(relative_dir, 'leaderboard')
    leaderboard_dir = p.join(root_dir, relative_leaderboard_dir)
    static_dir = p.join(leaderboard_dir, 'static')
    template_dir = p.join(leaderboard_dir, 'templates')
    relative_test_dir = p.join(relative_dir, 'test')
    test_dir = p.join(root_dir, relative_test_dir)
    is_test = 'IS_TEST' in os.environ
    dry_run = 'DRY_RUN' in os.environ
    force_gen = 'FORCE_GEN' in os.environ
    if dry_run:
        log.info('********* DRY RUN **********')
    should_mock_git = 'SHOULD_MOCK_GIT' in os.environ or is_test or dry_run
    should_mock_gcs = 'SHOULD_MOCK_GCS' in os.environ or is_test or dry_run
    gist_search_template = \
        'https://api.github.com/users/botleague-results/gists?since={time}'
    gcs_bucket = 'botleague.io'

    # This will change during tests
    relative_gen_parent = relative_leaderboard_dir

    # Properties that will change during tests
    # --------------------------------------------------------------------------
    @property
    def relative_gen_dir(self):
        return p.join(self.relative_gen_parent, 'generated')

    @relative_gen_dir.setter
    def relative_gen_dir(self, value):
        self.relative_gen_dir = value

    @property
    def gen_dir(self):
        return p.join(self.root_dir, self.relative_gen_dir)

    @property
    def relative_data_dir(self):
        if c.is_test:
            assert self.relative_gen_parent != self.relative_leaderboard_dir
        return p.join(self.relative_gen_parent, 'data')

    @property
    def data_dir(self):
        return p.join(self.root_dir, self.relative_data_dir)

    @property
    def relative_problem_dir(self):
        return p.join(self.relative_data_dir, 'problems')

    @property
    def problem_dir(self):
        ret = p.join(self.root_dir, self.relative_problem_dir)
        os.makedirs(ret, exist_ok=True)
        return ret

    @property
    def problem_html_dir(self):
        ret = p.join(self.gen_dir, 'problems')
        os.makedirs(ret, exist_ok=True)
        return ret

    @property
    def last_gist_time_filepath(self):
        return p.join(self.data_dir, 'last-generation-time.txt')

    @property
    def results_gist_ids_filepath(self):
        return p.join(self.data_dir, 'results_gist_ids.txt')

    @property
    def mock_gist_search(self):
        return read_json(p.join(c.data_dir, 'gists', 'searches.json'))

    # --------------------------------------------------------------------------


if 'GITHUB_DEBUG' in os.environ:
    github.enable_console_debug_logging()

c = Config()

if util.is_docker():
    os.environ['PATH'] = os.environ['PATH'] + \
                         ':/root/google-cloud-sdk/bin'
