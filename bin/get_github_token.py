# Disable logs so only token is printed to stdout
from leaderboard_generator import logs
logs.disabled = True

from leaderboard_generator.botleague_gcp.constants import GITHUB_TOKEN

print(GITHUB_TOKEN)
