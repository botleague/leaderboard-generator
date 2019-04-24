#!/usr/bin/env bash

watchmedo shell-command \
  --ignore-pattern="*/generated*;*/.idea*;*___*;" \
  --recursive \
  --command='echo file changed "${watch_src_path}"; python leaderboard_generator/gen.py' \
  --wait \
  --drop \
  --interval 5.0 \
   --ignore-directories \
  .
