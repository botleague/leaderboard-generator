import json
import os
import os.path as p

from botleague_helpers.config import blconfig

from leaderboard_generator.config import config
from github import Github, UnknownObjectException, Repository

from leaderboard_generator.util import read_json, read_file, write_file, \
    exists_and_unempty

from leaderboard_generator import logs

log = logs.get_log(__name__)


class ProblemBase:
    # Class constants
    RESULTS_FILENAME = 'aggregated_results.json'
    DEFINITION_FILENAME = 'problem.json'
    README_FILENAME = 'README.md'
    RELATIVE_DIR = 'problems'
    BL_REPO_ORG = 'deepdrive'
    BL_REPO_NAME = 'botleague'
    GITHUB: Repository = None

    # Instance variables
    id: str
    dir: str
    relative_dir: str
    results_filepath: str
    definition_filepath: str
    readme_filepath: str
    definition: dict
    readme: str

    def __init__(self, problem_id):
        """
        :param problem_id: The unique name, i.e. "domain_randomization" given
        to the problem. The problem must not change after others have submitted
        bots to be evaluated on it. Therefore, to create a variation
        of the "domain_randomization" problem, you'd create something like
        "domain_randomization_2" or "domain_randomization_with_traction".
        Problems are taggable, so grouping them in arbitrary ways is possible
        with tags, i.e. both of the above problems could be tagged under
        "domain-randomization"
        """
        self.id = problem_id
        self.relative_dir = p.join(config.relative_problem_dir, self.id)
        self.dir = p.join(config.root_dir, self.relative_dir)
        os.makedirs(self.dir, exist_ok=True)
        self.results_filepath = p.join(self.dir, self.RESULTS_FILENAME)
        self.definition_filepath = p.join(self.dir, self.DEFINITION_FILENAME)
        self.readme_filepath = p.join(self.dir, self.README_FILENAME)

        self.definition = {}
        self.readme = ''

    def fetch(self) -> bool:
        os.makedirs(self.dir, exist_ok=True)
        found_readme = self.fetch_readme()
        found_definition = self.fetch_definition()

        return found_definition and found_readme

    def fetch_readme(self) -> bool:
        if exists_and_unempty(self.readme_filepath):
            self.readme = read_file(self.readme_filepath)
            ret = bool(self.readme)
        else:
            readme = self.fetch_file(self.README_FILENAME)
            if readme:
                write_file(self.readme, self.readme_filepath)
                self.readme = readme
                ret = True
            else:
                log.error('No %s found for %s. Could not fetch',
                          self.README_FILENAME, self.id)
                ret = False

        return ret

    def fetch_definition(self) -> bool:
        if exists_and_unempty(self.definition_filepath):
            self.definition = read_json(self.definition_filepath)
            ret = True
        else:
            # New problem, get definition json from botleague
            # TODO: Don't allow this if submissions have been made by
            #  authors other than creator
            definition_str = self.fetch_file(self.DEFINITION_FILENAME)
            if not definition_str:
                log.error('No %s found for %s. Could not fetch',
                          self.DEFINITION_FILENAME, self.id)
                ret = False
            else:
                self.definition = json.loads(definition_str)
                write_file(definition_str, self.definition_filepath)
                ret = True
        return ret

    def fetch_file(self, filepath) -> str:
        raise NotImplementedError()

    def fetch_file(self, filepath) -> str:
        if not blconfig.is_test:
            ret = self.get_from_github(filepath)
        else:
            filepath = os.sep.join(filepath.split('/'))
            ret = read_file(p.join(config.mock_services_dir, 'github',
                                   self.BL_REPO_ORG,
                                   self.BL_REPO_NAME, self.RELATIVE_DIR,
                                   self.id, filepath))
        return ret




class Problem(ProblemBase):

    def get_from_github(self, filename):
        self.ensure_github_client()
        github = Problem.GITHUB
        relative_path = 'problems/{id}/{filename}'.format(id=self.id,
                                                          filename=filename)
        try:
            contents = github.get_contents(relative_path)
            content_str = contents.decoded_content.decode('utf-8')
        except UnknownObjectException:
            log.error('Unable to find %s in %s', relative_path, github.html_url)
            content_str = ''
        ret = content_str
        return ret

    def ensure_github_client(self):
        if Problem.GITHUB is None:
            from botleague_helpers.config import blconfig
            ProblemBase.GITHUB = Github(blconfig.github_token).\
                get_repo('%s/%s' % (self.BL_REPO_ORG, self.BL_REPO_NAME))