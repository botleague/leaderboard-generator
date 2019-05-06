import os.path as p

import git

import leaderboard_generator.constants as c

ROOT_DIR = p.dirname(p.dirname(p.realpath(__file__)))


class GitUtil(object):
    def __init__(self):
        self.repo = git.Repo(ROOT_DIR)
        self.git_cmd = self.repo.git

    def commit_and_push_leaderboard(self):
        self.git_cmd.commit('')


pass