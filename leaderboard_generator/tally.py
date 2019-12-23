
from copy import deepcopy

from leaderboard_generator import logs

log = logs.get_log(__name__)


def tally_bot_scores(results):
    results = deepcopy(results)
    results.sort(key=lambda x: x['utc_timestamp'])
    ret = {}
    for result in results:
        src_commit = result['source_commit']
        log.info('Processing source commit %s', src_commit)
        botname = result['botname']
        username = result['username']
        full_botname = '%s/%s' % (username, botname)
        if 'reason' in result and result['reason'] == 'problem_changed':
            log.info(f'Not counting score for {botname} from {username} - '
                     f'Was a CI test, not an eval initiated by user')
        elif 'is_release' in result and not result['is_release']:
            # This won't happen so long as we aren't including problem_changed
            # evals
            log.info(f'Not counting score for {botname} from {username} - '
                     f'Eval was on a non-release branch.')
        elif full_botname in ret:
            current = ret[full_botname]
            old_high_score = current['score']
            new_score = result['score']
            if old_high_score < new_score:
                ret[full_botname] = result
                log.info('New high score for bot %s of %r, old high '
                         'score was %r', full_botname, new_score,
                         old_high_score)
            elif old_high_score == new_score:
                if result['utc_timestamp'] < current['utc_timestamp']:
                    # Keep older result if tie
                    ret[full_botname] = result
                    log.info('New score for bot %s of %r ties old '
                             'high score. Ignoring new result.' %
                             (full_botname, new_score))
            else:
                log.info('New score for bot %s of %r is lower than '
                         'existing %r. Ignoring new results' %
                         (full_botname, new_score, old_high_score))
        else:
            log.info('Found new bot %s', full_botname)
            ret[full_botname] = result

    ret = list(ret.values())
    ret.sort(key=lambda x: x['score'], reverse=True)
    set_ranks(ret)
    return ret


def set_ranks(results):
    """
    Add rank to results considering ties
    @:param results (list): Sorted results
    """
    results[0]['rank'] = 1
    if len(results) > 1:
        for i in range(len(results) - 1):
            r1 = results[i]
            r2 = results[i+1]
            s1 = r1['score']
            s2 = r2['score']
            if s1 == s2:
                r2['rank'] = r1['rank']
            else:
                r2['rank'] = i + 2
    return results
