# Usage, see Makefile

FROM python:3.7
RUN curl -sSL https://sdk.cloud.google.com | bash
RUN mkdir leaderboard-generator
WORKDIR leaderboard-generator
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . .

# Make sure we have up to date github backed libs
RUN pip install --upgrade --force-reinstall --ignore-installed --no-cache-dir git+git://github.com/botleague/botleague-helpers#egg=botleague-helpers

RUN pip install -e .
CMD bin/run.sh

# TODO(post launch): To auto-deploy python changes, setup GCR build from GitHub and
#   restart instance
