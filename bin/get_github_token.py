# Disable logs so only token is printed to stdout
from leaderboard_generator import logs
logs.disabled = True

from botleague_helpers.config import blconfig

outfilename = '/tmp/.github_token'

token = blconfig.github_token

with open(outfilename, 'w') as outfile:
    outfile.write(token)

print(f'Wrote token "{token[:3]}..{token[-3:]}" to %s' % outfilename)
