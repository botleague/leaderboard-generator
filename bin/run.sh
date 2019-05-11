#!/usr/bin/env bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${DIR}/..

# Setup git auth
GITHUB_PASSWORD=`python -c 'import leaderboard_generator.config as c; print(c.GITHUB_TOKEN)'`
if [[ ${GITHUB_PASSWORD} = *[!\ ]* ]]; then
    echo Changing git remote to authorized HTTPS
    git remote rm origin
    git remote add origin https://crizcraig:${GITHUB_PASSWORD}@github.com/deepdrive/leaderboard-generator
else
  echo No GitHub token present, not changing remote
fi

# Check for latest leaderboard/ from github.
# This allows restarting the generator without rebuilding the docker
# image.
git fetch
git checkout master leaderboard_generator/leaderboard

python -c "import leaderboard_generator as g; g.main.main()"