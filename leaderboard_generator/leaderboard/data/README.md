#### Problem results

Aggregated results are stored here in the name of providing an open data 
leaderboard site.

In the event json files exceed git limits, we can store them in a public s3
bucket. In order to speed things up we can use simdjson and query parts of 
the JSON file we need. Such a simple database is fine since the results.json
files are quite small and just link out to where larger data is stored.

Also, we don't need to deal with asynchronous queries, since we just use
an event loop, that regenerates the site on a single thread when new
results come in.

We don't need anything more than that unless you wanted to provide some
multi-tag view which doesn't sound that useful. Folks can always
add different views as it's all open data, i.e. pushing out to BigQuery
like PyPi.