from leaderboard_generator.config import config

if config.dry_run:
    print('Confirmed')
else:
    raise RuntimeError('NOT DRY RUN')
