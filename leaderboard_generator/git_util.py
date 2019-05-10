import os.path as p
import logging as log

import git

import leaderboard_generator.config as c

ROOT_DIR = p.dirname(p.dirname(p.realpath(__file__)))


class GitUtil(object):
    def __init__(self):
        self.repo = git.Repo(ROOT_DIR)
        self.git_cmd = self.repo.git

    def commit_and_push_leaderboard(self):
        """
        Detects, commits, and pushes changes only to leaderboard site directory.
        @:return list of pushed filenames
        """
        ret = []
        self.git_cmd.reset()  # Unstage any dev changes
        self.git_cmd.add(c.SITE_DIR)
        if self.repo.is_dirty(path=c.SITE_DIR):
            ret = self.git_cmd.diff(
                '--name-only', '--cached', c.SITE_DIR).split()
            self.git_cmd.commit('-m autogen')
            self.git_cmd.push('origin', 'master')
        else:
            log.warning('No changes detected to leaderboard! - Not pushing')
        return ret


def main():
    git_util = GitUtil()
    git_util.commit_and_push_leaderboard()


if __name__ == '__main__':
    main()
