# ha-shellies-discovery - Docker Edition

DockerHub: [https://hub.docker.com/repository/docker/jlrgraham/ha-shellies-discovery](https://hub.docker.com/repository/docker/jlrgraham/ha-shellies-discovery)

This is a "dockerized" version of the code from: [https://github.com/bieniu/ha-shellies-discovery](https://github.com/bieniu/ha-shellies-discovery)

The goal here is to decouple the operation of the discovery publishing agent from Home Assistant.  My personal use case is to have this run as a distinct pod inside of a Kubernetes cluster.

## Configuration

All configuration elements are driven by environmental variables inside the container.

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `SHELLEY_ANNOUNCE_MQTT_PREFIX` | The prefix under which Shelly device(s) publish data. | `shellies` |
| `MQTT_BROKER` | The hostname or IP of the MQTT broker. | `mqtt` |
| `MQTT_PORT` | The connection port on the MQTT broker.  If set to 8883 TLS is automatically used. | 8883 |
| `MQTT_CLIENT_ID` | The client name given to the MQTT broker.  See MQTT Connections for more details. | `ha-shellies-discovery` |
| `MQTT_USERNAME` | The username for the MQTT broker. | `None` |
| `MQTT_PASSWORD` | The password for the MQTT broker. | `None` |
| `HA_DISCOVERY_PREFIX` | The configured Home Assistant discovery prefix. | `homeassistant` |


### MQTT Connections

#### Authentication

Authentication will be attempted only if both `MQTT_USERNAME` and `MQTT_PASSWORD` are supplied.

#### Client ID

The MQTT client ID can be configured with the `MQTT_CLIENT_ID` variable.  This should generally be fixed for a given deployment.

#### TLS

If the MQTT broker port configuration is set to 8883 then the connector will automatically attempt to enable TLS for the connection to the broker.  The standard [Python certifi package](https://pypi.org/project/certifi/) will be used for CA roots, so public certs (ie: Let's Encrypt + others) should just work.
