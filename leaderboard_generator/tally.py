
from copy import deepcopy

from leaderboard_generator import logs

log = logs.get_log(__name__)


def tally_bot_scores(results):

    results = deepcopy(results)

    results.sort(key=lambda x: x['utc_timestamp'])

    ret = {}
    url_prefix = 'https://github.com/'
    for result in results:
        url = result['agent_source_commit']
        if not url.startswith(url_prefix):
            log.error('Skipping submission with github url in incorrect '
                      'format: %s' % url)
        else:
            log.info('Processing agent source commit %s', url)
            url_parts = url[len(url_prefix):].split('/')
            username, repo_name = url_parts[:2]

            # Add username and repo name to stored results
            result['username'], result['repo_name'] = username, repo_name

            botname = '%s/%s' % (username, repo_name)
            if botname in ret:
                current = ret[botname]
                old_high_score = current['score']
                new_score = result['score']
                if old_high_score < new_score:
                    ret[botname] = result
                    log.info('New high score for bot %s of %r, old high '
                             'score was %r', botname, new_score, old_high_score)
                elif old_high_score == new_score:
                    if result['utc_timestamp'] < current['utc_timestamp']:
                        # Keep older result if tie
                        ret[botname] = result
                        log.info('New score for bot %s of %r ties old '
                                 'high score. Ignoring new result.' %
                                 (botname, new_score))
                else:
                    log.info('New score for bot %s of %r is lower than '
                             'existing %r. Ignoring new results' %
                             (botname, new_score, old_high_score))
            else:
                log.info('Found new bot %s!', botname)
                ret[botname] = result

    # Add botname to result
    for r in ret:
        ret[r]['botname'] = r

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
