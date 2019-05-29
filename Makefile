.PHONY: build push run bash test deploy reboot_vm

TAG=gcr.io/silken-impulse-217423/leaderboard-generator
SSH=gcloud compute ssh leaderboard-generator-1

build:
	docker build -t $(TAG) .

push:
	docker push $(TAG)

test:
	docker run -it $(TAG) bin/test.sh

ssh:
	$(SSH)

reboot_vm:
	$(SSH) --command "echo connection successful"
	$(SSH) --command "sudo reboot" || echo "Rebooted VM. Expected exit error above!"

deploy: build test push reboot_vm

run:
	docker run -it $(TAG)

bash:
	docker run -it $(TAG) bash