#!/usr/bin/env bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd DIR../

git fetch
git checkout HEAD leaderboard_generator/leaderboard