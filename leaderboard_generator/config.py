import os
import os.path as p

import github
from botleague_helpers.config import blconfig

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
    dry_run = 'DRY_RUN' in os.environ
    force_gen = 'FORCE_GEN' in os.environ
    regen_no_cache = 'REGEN_NO_CACHE' in os.environ
    if dry_run:
        log.info('********* DRY RUN **********')
    is_test = blconfig.is_test
    should_mock_git = 'SHOULD_MOCK_GIT' in os.environ or is_test or dry_run
    should_mock_gcs = 'SHOULD_MOCK_GCS' in os.environ or is_test or dry_run
    should_mock_github = 'SHOULD_MOCK_GITHUB' in os.environ or is_test or \
                         dry_run
    gist_search_template = \
        'https://api.github.com/users/botleague-results/gists?since={time}'
    gcs_bucket = 'botleague.io'

    # Properties that will change during tests
    # --------------------------------------------------------------------------
    # TODO(post launch): Auto change this using botleague-helpers get_test_name_from_callstack
    relative_gen_parent = relative_leaderboard_dir

    @property
    def gen_parent(self):
        return p.join(self.root_dir, self.relative_gen_parent)

    @property
    def relative_gen_dir(self):
        return p.join(self.relative_gen_parent, 'generated')

    @property
    def gen_dir(self):
        ret = p.join(self.root_dir, self.relative_gen_dir)
        os.makedirs(ret, exist_ok=True)
        return ret

    @property
    def relative_site_dir(self):
        return p.join(self.relative_gen_dir, 'site')

    @property
    def site_dir(self):
        ret = p.join(self.root_dir, self.relative_site_dir)
        # Don't create as we need to copytree and it doesn't like an empty dir
        # there.
        return ret

    @property
    def relative_data_dir(self):
        if blconfig.is_test:
            assert self.relative_gen_parent != self.relative_leaderboard_dir
        return p.join(self.relative_gen_dir, 'data')

    @property
    def data_dir(self):
        ret = p.join(self.root_dir, self.relative_data_dir)
        os.makedirs(ret, exist_ok=True)
        return ret

    @property
    def relative_problem_dir(self):
        return p.join(self.relative_data_dir, 'problems')

    @property
    def problem_dir(self):
        ret = p.join(self.root_dir, self.relative_problem_dir)
        os.makedirs(ret, exist_ok=True)
        return ret

    @property
    def relative_gist_dir(self):
        return p.join(self.relative_data_dir, 'gist')

    @property
    def gist_dir(self):
        ret = p.join(self.root_dir, self.relative_problem_dir)
        os.makedirs(ret, exist_ok=True)
        return ret

    @property
    def problem_html_dir(self):
        ret = p.join(self.site_dir, 'problems')
        os.makedirs(ret, exist_ok=True)
        return ret

    @property
    def last_gist_time_filepath(self):
        return p.join(self.data_dir, 'last-gist-time.txt')

    @property
    def results_gist_ids_filepath(self):
        return p.join(self.data_dir, 'results_gist_ids.txt')

    @property
    def mock_services_dir(self):
        ret = p.join(config.relative_gen_parent, 'mock_services')
        os.makedirs(ret, exist_ok=True)
        return ret

    @property
    def mock_gist_search(self):
        return read_json(p.join(self.mock_services_dir,
                                'gists', 'searches.json'))

    # --------------------------------------------------------------------------


if 'GITHUB_DEBUG' in os.environ:
    github.enable_console_debug_logging()

config = Config()


def add_gcloud_sdk_to_path():
    if util.is_docker():
        gcloud_sdk_path = '/root/google-cloud-sdk/bin'
        log.info('Detected we are in docker, adding %s to PATH',
                 gcloud_sdk_path)
        os.environ['PATH'] = os.environ['PATH'] + ':' + gcloud_sdk_path


add_gcloud_sdk_to_path()
