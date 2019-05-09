import os.path as p

from datetime import datetime

ROOT_DIR = p.dirname(p.dirname(p.realpath(__file__)))
LEADERBOARD_DIR = p.join(ROOT_DIR, 'leaderboard_generator', 'leaderboard')
GEN_DIR = p.join(LEADERBOARD_DIR, 'generated')
LAST_GEN_FILEPATH = p.join(GEN_DIR, 'last-generation-time.json')

GIST_SEARCH = 'https://api.github.com/users/botleague-results/gists?since={time}'
SITE_DIR = 'leaderboard_generator/leaderboard'

