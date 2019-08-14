# Usage, see Makefile

# Run: docker run -it deepdriveio/leaderboard-generator
# or   docker run -e SHOULD_USE_FIRESTORE=false -it deepdriveio/leaderboard-generator
FROM python:3.7
RUN curl -sSL https://sdk.cloud.google.com | bash
RUN mkdir leaderboard-generator
WORKDIR leaderboard-generator
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . .
RUN pip install -e .
CMD bin/run.sh

# TODO(post launch): To auto-deploy python changes, setup GCR build from GitHub and
#   restart instance
