# Disable logs so only token is printed to stdout
from leaderboard_generator import logs
logs.disabled = True

from botleague_helpers.constants import GITHUB_TOKEN

print(GITHUB_TOKEN)
