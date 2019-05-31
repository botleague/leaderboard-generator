# Disable logs so only token is printed to stdout
from leaderboard_generator import logs
logs.disabled = True

from botleague_helpers.config import blconfig

print(blconfig.github_token)
