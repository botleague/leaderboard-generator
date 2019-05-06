import os.path as p

import git

import leaderboard_generator.constants as c

ROOT_DIR = p.dirname(p.dirname(p.realpath(__file__)))


class GitUtil(object):
    def __init__(self):
        self.repo = git.Repo(ROOT_DIR)
        self.git_cmd = self.repo.git

    def commit_and_push_leaderboard(self):
        self.git_cmd.commit('-am "autogen" leaderboard')
        self.git_cmd.push('origin', 'master')


def main():
    git_util = GitUtil()
    git_util.commit_and_push_leaderboard()


if __name__ == '__main__':
    main()