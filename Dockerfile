# Build: docker build -t leaderboard-generator .
# Run: docker run -it leaderboard-generator
# or   docker run -e SHOULD_USE_FIRESTORE=false -it leaderboard-generator
FROM python:3
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
COPY . .
WORKDIR .
CMD python poll_for_results.py