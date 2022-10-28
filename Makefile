DOCKER_IMAGE ?= jlrgraham/ha-shellies-discovery
DOCKER_TAG ?= latest

DOCKER_NAME := $(DOCKER_IMAGE):$(DOCKER_TAG)

build:
	docker build --tag $(DOCKER_NAME) .

push:
	docker push $(DOCKER_NAME)

run:
	docker run \
		-it \
		--rm \
		-e LOG_LEVEL=DEBUG \
		-e MQTT_BROKER \
		-e MQTT_USERNAME \
		-e MQTT_PASSWORD \
		-e HA_DISCOVERY_PREFIX \
		$(DOCKER_NAME)
