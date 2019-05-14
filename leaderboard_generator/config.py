import os
import os.path as p
import sys

from datetime import datetime
import github

SHOULD_MOCK_GIT = 'SHOULD_MOCK_GIT' in os.environ
SHOULD_MOCK_GCS = 'SHOULD_MOCK_GCS' in os.environ
IS_TEST = 'IS_TEST' in os.environ

ROOT_DIR = p.dirname(p.dirname(p.realpath(__file__)))
RELATIVE_DIR = 'leaderboard_generator'
RELATIVE_LEADERBOARD_DIR = p.join(RELATIVE_DIR, 'leaderboard')
LEADERBOARD_DIR = p.join(ROOT_DIR, RELATIVE_LEADERBOARD_DIR)
STATIC_DIR = p.join(LEADERBOARD_DIR, 'static')
TEMPLATE_DIR = p.join(LEADERBOARD_DIR, 'templates')
GEN_DIR = p.join(LEADERBOARD_DIR, 'generated')
GEN_PROBLEM_DIR = p.join('problems', 'generated')
GEN_USERS_DIR = p.join('users', 'generated')
GEN_CHALLENGES_DIR = p.join('challenges', 'generated')
RELATIVE_TEST_DIR = p.join(RELATIVE_DIR, 'test')
TEST_DIR = p.join(ROOT_DIR, RELATIVE_TEST_DIR)
if IS_TEST:
    RELATIVE_DATA_DIR = p.join(RELATIVE_TEST_DIR, 'data')
else:
    RELATIVE_DATA_DIR = p.join(RELATIVE_LEADERBOARD_DIR, 'data')
DATA_DIR = p.join(ROOT_DIR, RELATIVE_DATA_DIR)
LAST_GEN_FILEPATH = p.join(DATA_DIR, 'last-generation-time.txt')
RESULTS_GIST_IDS_FILEPATH = p.join(DATA_DIR, 'results_gist_ids.txt')

GIST_SEARCH = 'https://api.github.com/users/botleague-results/gists?since={time}'
RELATIVE_SITE_DIR = 'leaderboard_generator/leaderboard'
SITE_DIR = p.join(ROOT_DIR, RELATIVE_SITE_DIR)

if 'GITHUB_DEBUG' in os.environ:
    github.enable_console_debug_logging()
