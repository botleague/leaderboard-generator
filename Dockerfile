# Build: docker build -t deepdriveio/leaderboard-generator .
# Push: docker push gcr.io/silken-impulse-217423/leaderboard-generator
# Run: docker run -it deepdriveio/leaderboard-generator
# or   docker run -e SHOULD_USE_FIRESTORE=false -it deepdriveio/leaderboard-generator
FROM python:3
RUN mkdir leaderboard-generator
WORKDIR leaderboard-generator
COPY . .
RUN pip install -e .
CMD bin/run.sh

# TODO: To auto-deploy python changes, setup GCR build from GitHub and
#   restart instance