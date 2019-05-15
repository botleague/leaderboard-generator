.PHONY: build push run bash

TAG=gcr.io/silken-impulse-217423/leaderboard-generator

build:
	docker build -t $(TAG) .

push:
	docker push $(TAG)

run:
	docker run -it $(TAG)

bash:
	docker run -it $(TAG) bash