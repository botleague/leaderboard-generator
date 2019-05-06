# Build: docker build -t deepdriveio/leaderboard-generator .
# Run: docker run -it deepdriveio/leaderboard-generator
# or   docker run -e SHOULD_USE_FIRESTORE=false -it deepdriveio/leaderboard-generator
FROM python:3
RUN mkdir leaderboard-generator
WORKDIR leaderboard-generator
COPY requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
COPY . .
CMD python ./leaderboard_generator/main.py