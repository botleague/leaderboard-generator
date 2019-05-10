import os
import os.path as p

from datetime import datetime
import github

ROOT_DIR = p.dirname(p.dirname(p.realpath(__file__)))
LEADERBOARD_DIR = p.join(ROOT_DIR, 'leaderboard_generator', 'leaderboard')
GEN_DIR = p.join(LEADERBOARD_DIR, 'generated')
GEN_PROBLEM_DIR = p.join('problems', 'generated')
GEN_USERS_DIR = p.join('users', 'generated')
GEN_CHALLENGES_DIR = p.join('challenges', 'generated')
DATA_DIR = p.join(LEADERBOARD_DIR, 'data')
LAST_GEN_FILEPATH = p.join(DATA_DIR, 'last-generation-time.txt')
RESULTS_GIST_IDS_FILEPATH = p.join(DATA_DIR, 'results_gist_ids.txt')

GIST_SEARCH = 'https://api.github.com/users/botleague-results/gists?since={time}'
SITE_DIR = 'leaderboard_generator/leaderboard'

if 'GITHUB_DEBUG' in os.environ:
    github.enable_console_debug_logging()


