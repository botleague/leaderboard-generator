import logging as log


def tally_bot_scores(results):

    # Keep older bots if tie
    results.sort(key=lambda x: x['utc_timestamp'])

    ret = {}
    url_prefix = 'https://github.com/'
    for result in results:
        url = result['agent_source_commit']
        if not url.startswith(url_prefix):
            log.error('Skipping submission with github url in incorrect '
                      'format: %s' % url)
        else:
            botname = url[len(url_prefix):].split('/')[1]
            if botname in ret:
                current = ret[botname]
                if current['score'] < result['score']:
                    ret[botname] = result
            else:
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
