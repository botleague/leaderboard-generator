import json
import os
import os.path as p

from botleague_helpers.config import blconfig

from leaderboard_generator.config import config

from leaderboard_generator.models.base import Base
from leaderboard_generator.util import read_json, read_file, write_file, \
    exists_and_unempty

from leaderboard_generator import logs

log = logs.get_log(__name__)


class ProblemBase(Base):
    # Class constants
    RESULTS_FILENAME = 'aggregated_results.json'
    DEFINITION_FILENAME = 'problem.json'
    README_FILENAME = 'README.md'
    RELATIVE_DIR = 'problems'

    # Instance variables
    id: str
    dir: str
    relative_dir: str
    results_filepath: str
    definition_filepath: str
    readme_filepath: str
    definition: dict
    readme: str

    def __init__(self, problem_id: str):
        """
        :param problem_id: The unique name, i.e.
        "deepdrive/domain_randomization" given
        to the problem.
        Problems are taggable, so grouping them in arbitrary ways is possible
        with tags, i.e. both of the above problems could be tagged under
        "domain-randomization"
        """
        self.id = problem_id
        self.relative_dir = p.join(config.relative_problem_dir, self.id)
        self.dir = p.join(config.root_dir, self.relative_dir)
        os.makedirs(self.dir, exist_ok=True)
        self.results_filepath = p.join(self.dir, cls.RESULTS_FILENAME)
        self.definition_filepath = p.join(self.dir, cls.DEFINITION_FILENAME)
        self.readme_filepath = p.join(self.dir, cls.README_FILENAME)

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
            readme = self.fetch_file(Problem.README_FILENAME)
            if readme:
                write_file(self.readme_filepath, self.readme)
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
                write_file(self.definition_filepath, definition_str)
                ret = True
        return ret

    def fetch_file(self, filepath) -> str:
        raise NotImplementedError()


class Problem(ProblemBase):

    def fetch_file(self, filename) -> str:
        if not blconfig.is_test:
            relative_path = 'problems/{id}/{filename}'.format(
                id=self.id,
                filename=filename)
            ret = self.get_from_github(relative_path)
        else:
            filename = os.sep.join(filename.split('/'))
            ret = read_file(p.join(config.mock_services_dir, 'github',
                                   self.BL_REPO_ORG, self.BL_REPO_NAME,
                                   self.RELATIVE_DIR, self.id, filename))
        return ret

