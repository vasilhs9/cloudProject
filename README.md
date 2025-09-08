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
