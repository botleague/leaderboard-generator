import os.path as p
import git
from botleague_helpers.config import blconfig

from leaderboard_generator.config import config
from leaderboard_generator import logs

log = logs.get_log(__name__)

ROOT_DIR = p.dirname(p.dirname(p.realpath(__file__)))


class AutoGitBase(object):
    """
    Automatically versions data and generated HTML
    """
    def __init__(self):
        self.repo = git.Repo(ROOT_DIR)
        self.git = self.repo.git

    def push(self):
        raise NotImplementedError()

    def commit(self, commit_args):
        raise NotImplementedError()

    @property
    def paths(self):
        # Set of paths that contain automatically created data which
        # we wish to version control
        return [config.relative_gen_dir]

    def commit_and_push(self):
        """
        Pushes automatically generated/created files so that data & code
        are versioned together.
        @:return list of pushed filenames
        """
        ret = []
        for relative_path in self.paths:
            self.git.add(relative_path)
            if self.repo.is_dirty(path=relative_path):
                filenames = self.get_staged_changes(relative_path)
                commit_args = '-m autogen %s' % relative_path
                log.info('git commit %s', commit_args)
                log.info('Running git commit on:\n\t%s', '\n\t'.join(filenames))
                self.commit(commit_args)
                ret += filenames
            else:
                log.debug('No changes detected to %s, not committing',
                          relative_path)
        if ret:
            log.info('Pushing changed files to github:\n\t%s', '\n\t'.join(ret))
            self.push()

        # TODO: Deal with deleted files? Assuming this can't happen since
        #  new results will just create files (in the case of new problems)
        #  or modify them, in which case it's fine to add and commit.
        #  Deleting files will happen externally and come in via run.sh
        #  pulling new GitHub changes on VM restart. Deleted files during
        #  results processing should cause an error as we will attempt to
        #  upload the missing files to GCP as they have been "changed" per git.

        return ret

    def get_staged_changes(self, relative_path):
        filenames = self.git.diff(
            '--name-only', '--cached', relative_path).split()
        return filenames

    def reset_generated_files_hard(self):
        if not blconfig.is_test and not config.dry_run:
            log.error('Not expecting to reset generated files outside tests '
                      'or dry runs')
        else:
            self.repo.head.reset(paths=self.paths)
            for path in self.paths:
                self.git.clean('-df', path)


class AutoGit(AutoGitBase):
    def __init__(self):
        super().__init__()

    def commit(self, commit_args):
        return self.git.commit(commit_args)

    def push(self):
        ret = self.git.push('origin', 'master')
        log.info('Pushed to master')
        return ret


class AutoGitMock(AutoGitBase):
    """Runs things locally then resets for testing purposes"""
    def commit(self, commit_args):
        log.info('Would have committed with args "%s", but we are testing!',
                 commit_args)

    def push(self):
        log.info('Would have pushed, but we are testing!')

    def __init__(self):
        super().__init__()


def get_auto_git() -> AutoGitBase:
    if config.should_mock_git:
        return AutoGitMock()
    else:
        return AutoGit()
