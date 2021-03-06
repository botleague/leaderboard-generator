.PHONY: build push run bash test deploy reboot_vm prepare

TAG=gcr.io/silken-impulse-217423/leaderboard-generator
SSH=gcloud compute ssh leaderboard-generator-1

build:
	docker build -t $(TAG) .

push:
	docker push $(TAG)

test: build
	docker run -it $(TAG) bin/test.sh

ssh:
	$(SSH)

logs:
	$(SSH) --command "sudo docker logs klt-leaderboard-generator-1-ikku --tail 500 --follow"

prepare:
	$(SSH) --command "sudo docker image prune -f"
	$(SSH) --command "sudo docker container prune -f"

reboot_vm:
	$(SSH) --command "echo connection successful"
	$(SSH) --command "sudo reboot" || echo "\e[1;30;48;5;82m SUCCESS \e[0m Error above is due to reboot. You'll be able to run 'make ssh' again in a few seconds."

deploy: build test push prepare reboot_vm

run:
	docker run -it $(TAG)

bash:
	docker run -it $(TAG) bash

serve:
	PORT=8899 python bin/serve.py

autogen:
	python bin/autogen.py
