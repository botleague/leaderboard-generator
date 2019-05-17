#!/usr/bin/env bash

set -ev

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${DIR}/..

# Setup git auth
GITHUB_PASSWORD=`python bin/get_github_token.py`

if [[ ${GITHUB_PASSWORD} = *[!\ ]* ]]; then
    echo Changing git remote to authorized HTTPS
    git remote rm origin || echo no origin, adding
    git remote add origin https://crizcraig:${GITHUB_PASSWORD}@github.com/deepdrive/leaderboard-generator
else
  echo No GitHub token present, not changing remote
fi

python bin/run_main.py