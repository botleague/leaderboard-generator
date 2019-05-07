import os.path as p

import git

ROOT_DIR = p.dirname(p.dirname(p.realpath(__file__)))


class GitUtil(object):
    def __init__(self):
        self.repo = git.Repo(ROOT_DIR)
        self.git_cmd = self.repo.git

    def commit_and_push_leaderboard(self):
        self.git_cmd.add('leaderboard_generator/leaderboard')
        self.git_cmd.commit('-m autogen')
        self.git_cmd.push('origin', 'master')


def main():
    git_util = GitUtil()
    git_util.commit_and_push_leaderboard()


if __name__ == '__main__':
    main()
