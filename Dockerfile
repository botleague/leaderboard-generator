# Build: docker build -t deepdriveio/leaderboard-generator .
# Run: docker run -it deepdriveio/leaderboard-generator
# or   docker run -e SHOULD_USE_FIRESTORE=false -it deepdriveio/leaderboard-generator
FROM python:3
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
COPY . .
WORKDIR .
CMD python leaderboard_generator/poll_for_results.py