from leaderboard_generator.config import c

if c.dry_run:
    print('Confirmed')
else:
    raise RuntimeError('NOT DRY RUN')
