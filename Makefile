DOCKER_IMAGE ?= jlrgraham/ha-shellies-discovery
DOCKER_TAG ?= latest

DOCKER_NAME := $(DOCKER_IMAGE):$(DOCKER_TAG)

build:
	docker buildx \
		$@ \
		--platform linux/amd64,linux/arm64 \
		--tag $(DOCKER_NAME) \
		.
push:
	docker $@ $(DOCKER_NAME)

run:
	docker $@ \
		-it \
		--rm \
		-e LOG_LEVEL=DEBUG \
		-e MQTT_BROKER \
		-e MQTT_USERNAME \
		-e MQTT_PASSWORD \
		-e HA_DISCOVERY_PREFIX \
		$(DOCKER_NAME)

black:
	docker run \
		-it \
		--rm \
		-v ${PWD}:/app \
		--workdir /app \
		python:3 \
		bash -c "pip install black && black run.py"
