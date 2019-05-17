.PHONY: build push run bash test

TAG=gcr.io/silken-impulse-217423/leaderboard-generator

build:
	docker build -t $(TAG) .

push:
	docker push $(TAG)

test:
	docker run -it $(TAG) bin/test.sh

deploy: build test push
# TODO: Add GCE instance restart here

run:
	docker run -it $(TAG)

bash:
	docker run -it $(TAG) bash