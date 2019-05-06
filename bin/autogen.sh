#!/usr/bin/env bash

# Run this if you're developing HTML changes locally to avoid running generate
# all the time.

set -e

gen_cmd="python leaderboard_generator/gen.py"

# Generate on start
eval "${gen_cmd}"

watch_cmd="echo file changed \${watch_src_path}; ${gen_cmd}"

# Generate on file change
watchmedo shell-command \
  --ignore-pattern="*/generated*;*/.idea*;*___*;./.git*" \
  --recursive \
  --command="${watch_cmd}"
  --wait \
  --drop \
  --interval 5.0 \
   --ignore-directories \
  .
