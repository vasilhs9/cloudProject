# IoT Docker Project

This project contains multiple services communicating together:

- **Python App** – sends/receives data via RabbitMQ
- **Node-RED** – recieves data from weather api. Sends data to minio. Sends/recieves data to and from python app. Sends data to thingsboard
- **ThingsBoard CE** – visual representation of nodered/pythonapp data
- **Postgres** – database
- **RabbitMQ** – message broker
- **MinIO** – object storage

---

## Setup

1. **Clone the repository:**
```bash
git clone https://github.com/vasilhs9/cloudProject.git
cd cloudProject
docker compose run --rm -e INSTALL_TB=true -e LOAD_DEMO=true thingsboard-ce
```
2. **Start the containers (if python app does not start use the command twice)**
```bash
docker compose up -d
```
3. **Set up thingsboard**
Go to thingsboard (as a tenant) -> create new device named nodered-device -> copy access token from device details to node red username in security tab on mqtt out node
```bash
docker run --rm -it --add-host=host.docker.internal:host-gateway thingsboard/mosquitto-clients mosquitto_pub -d -q 1 -h host.docker.internal -p 1884 -t v1/devices/me/telemetry -u "aJSIa83n9QsqnGgPdkwM" -m "{temperature:25}"
```
Dashboards -> import aegina_weather.json -> edit the widgets to use nodered device

4. **Credentials**

THINGSBOARD:

address: http://localhost:8080
System Administrator: sysadmin@thingsboard.org / sysadmin
Tenant Administrator: tenant@thingsboard.org / tenant
Customer User: customer@thingsboard.org / customer

RABBITMQ:

address: http://localhost:15672
username: guest
password: guest

MINIO:

address: http://localhost:9090
username: admin
password: admin123

NODE RED:

address: http://localhost:1880
