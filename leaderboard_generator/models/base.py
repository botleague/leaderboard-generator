import time
from typing import List, Dict

from github import Repository, UnknownObjectException, Github, ContentFile, \
    RateLimitExceededException

from leaderboard_generator import logs

log = logs.get_log(__name__)


class Base:
    BL_REPO_ORG = 'botleague'
    BL_REPO_NAME = 'botleague'
    GITHUB: Repository = None

    # Mapping from path to file contents
    # TODO: We should just keep a local copy of the botleague repo and pull it,
    #   everytime should gen is set.
    LEAGUE_REPO_CONTENTS: Dict[str, str] = {}

    def get_from_github(self, relative_path):
        self.ensure_github_client()
        self.ensure_repo_contents()
        if relative_path in self.LEAGUE_REPO_CONTENTS:
            ret = self.LEAGUE_REPO_CONTENTS[relative_path]
        else:
            log.error('Unable to find %s in %s', relative_path,
                      self.GITHUB.html_url)
            ret = ''
        return ret

    def ensure_github_client(self):
        if Base.GITHUB is None:
            from botleague_helpers.config import blconfig
            Base.GITHUB = Github(blconfig.github_token).\
                get_repo('%s/%s' % (self.BL_REPO_ORG, self.BL_REPO_NAME))

    def ensure_repo_contents(self):
        if not Base.LEAGUE_REPO_CONTENTS:
            self.get_file_contents_in_dir_iterative('/')

    def github_get_dir_contents(self, directory: str):
        try:
            ret = self.GITHUB.get_dir_contents(directory)
            Base.GITHUB_SLEEP_TIME = 5
        except RateLimitExceededException:
            log.error('Received rate limit exception from GitHub, sleeping for '
                      '%r seconds', Base.GITHUB_SLEEP_TIME)
            time.sleep(Base.GITHUB_SLEEP_TIME)
            Base.GITHUB_SLEEP_TIME *= 2
            ret = self.github_get_dir_contents(directory)
        return ret

    def get_file_contents_in_dir_recursive(self, directory: str):
        contents = self.github_get_dir_contents(directory)
        for item in contents:
            if item.type == 'dir':
                self.get_file_contents_in_dir_recursive(item.path)
            else:
                Base.LEAGUE_REPO_CONTENTS[item.path] = \
                    item.decoded_content.decode('utf-8')

    def get_file_contents_in_dir_iterative(self, directory: str):
        contents = self.github_get_dir_contents(directory)
        todo = {con.path: con for con in contents}
        while todo:
            item = todo.pop(next(iter(todo)))
            if item.type == 'file':
                Base.LEAGUE_REPO_CONTENTS[item.path] = \
                    item.decoded_content.decode('utf-8')
            elif item.type == 'dir':
                new_contents = self.github_get_dir_contents(item.path)
                todo.update({con.path: con for con in new_contents})
            else:
                log.warning('Unexpected item type %s', item.type)


def clear_cached_botleague_repo_contents():
    Base.LEAGUE_REPO_CONTENTS = {}


if __name__ == '__main__':
    b = Base()
    c = b.get_from_github('problems/deepdrive/domain_randomization/README.md')
    pass

