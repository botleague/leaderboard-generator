import json
import os
import os.path as p

import leaderboard_generator.config as c
from github import Github

from leaderboard_generator.botleague_gcp.constants import GITHUB_TOKEN
from leaderboard_generator.util import load_json, read_file, write_file, \
    exists_and_unempty

from leaderboard_generator import logs

log = logs.get_log(__name__)


class Problem:
    RESULTS_FILENAME = 'aggregated_results.json'
    DEFINITION_FILENAME = 'problem.json'
    README_FILENAME = 'README.md'
    RELATIVE_DIR = 'problems'
    DIR = p.join(c.DATA_DIR, RELATIVE_DIR)
    GITHUB = Github(GITHUB_TOKEN).get_repo('deepdrive/botleague')

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
        self.dir = p.join(Problem.DIR, problem_id)
        os.makedirs(self.dir, exist_ok=True)
        self.relative_dir = p.join(Problem.RELATIVE_DIR, problem_id)
        self.results_filepath = p.join(self.dir, Problem.RESULTS_FILENAME)
        self.definition_filepath = p.join(self.dir, Problem.DEFINITION_FILENAME)
        self.readme_filepath = p.join(self.dir, Problem.README_FILENAME)

        self.definition = {}
        self.readme = ""

    def fetch(self):
        if exists_and_unempty(self.definition_filepath):
            self.definition = load_json(self.definition_filepath)
            self.readme = read_file(self.readme_filepath)
        else:
            # New problem, get definition json from botleague
            # TODO: Don't allow this if submissions have been made by
            #  authors other than creator
            definition_str = self.github_get(self.DEFINITION_FILENAME)
            self.definition = json.loads(definition_str)
            readme = self.github_get(Problem.README_FILENAME)
            write_file(definition_str, self.definition_filepath)
            write_file(readme, self.readme_filepath)
        return self

    def github_get(self, path):
        github = Problem.GITHUB
        contents = github.get_contents(self.relative_dir + '/' + path)
        content_str = contents.decoded_content.decode('utf-8')
        return content_str
