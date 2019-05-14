import os.path as p
import git

import leaderboard_generator.config as c
from leaderboard_generator import logs

log = logs.get_log(__name__)

ROOT_DIR = p.dirname(p.dirname(p.realpath(__file__)))


class AutoGitBase(object):

    # Set of paths that contain automatically created data which
    # we wish to version control
    PATHS = [c.RELATIVE_DATA_DIR, c.RELATIVE_SITE_DIR]

    def __init__(self):
        self.repo = git.Repo(ROOT_DIR)
        self.git = self.repo.git

    def push(self):
        raise NotImplementedError()

    def commit(self, commit_args):
        raise NotImplementedError()

    def commit_and_push(self):
        """
        Pushes automatically generated/created files so that data & code
        are versioned together.
        @:return list of pushed filenames
        """
        ret = []
        for relative_path in self.PATHS:
            self.git.add(relative_path)
            if self.repo.is_dirty(path=relative_path):
                filenames = self.get_changed_filenames(relative_path)
                commit_args = '-m autogen %s' % relative_path
                log.info('Running git commit on:\n\t%s', '\n\t'.join(filenames))
                log.info('git commit %s', commit_args)
                self.commit(commit_args)
                ret += filenames
            else:
                log.warning('No changes detected to %s, not committing',
                            relative_path)
        if ret:
            log.info('Pushing to master')
            self.push()
            log.info('Pushed changed files to github:\n\t%s', '\n\t'.join(ret))

        # TODO: Deal with deleted files? Assuming this can't happen since
        #  new results will just create files (in the case of new problems)
        #  or modify them, in which case it's fine to add and commit.
        #  Deleting files will happen externally and come in via run.sh
        #  pulling new GitHub changes on VM restart. Deleted files during
        #  results processing should cause an error as we will attempt to
        #  upload the missing files to GCP as they have been "changed" per git.

        return ret

    def get_changed_filenames(self, relative_path):
        filenames = self.git.diff(
            '--name-only', '--cached', relative_path).split()
        return filenames

    def reset(self, hard=False):
        self.repo.head.reset(paths=self.PATHS)


class AutoGit(AutoGitBase):
    def __init__(self):
        super().__init__()

    def commit(self, commit_args):
        return self.git.commit(commit_args)

    def push(self):
        return self.git.push('origin', 'master')


class AutoGitMock(AutoGitBase):
    """Runs things locally then resets for testing purposes"""
    def commit(self, commit_args):
        log.info('Would have committed with args %s, but we are testing!',
                 commit_args)

    def push(self):
        log.info('Would have pushed, but we are testing!')

    def __init__(self):
        super().__init__()


def get_auto_git() -> AutoGitBase:
    if c.SHOULD_MOCK_GIT:
        return AutoGitMock()
    else:
        return AutoGit()
