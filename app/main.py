import json
import pika
import boto3
from datetime import datetime


RABBITMQ_HOST = "rabbitmq"
RAW_QUEUE = "weather_queue"
PROCESSED_QUEUE = "processed_queue"

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin123"
BUCKET_NAME = "weather-data"

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1"
)

def ensure_bucket():
    buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if BUCKET_NAME not in buckets:
        s3.create_bucket(Bucket=BUCKET_NAME)

ensure_bucket()

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()

channel.queue_declare(queue=RAW_QUEUE, durable=True)
channel.queue_declare(queue=PROCESSED_QUEUE, durable=True)

def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode("utf-8"))

        # placeholder for processing data before saving
        temp = data.get("temperature")
        data["status"] = "good" if temp is not None and temp <= 25 else "bad"

        # timestamped filename for MinIO
        filename = f"weather_{datetime.utcnow().isoformat()}.json"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=json.dumps(data, indent=2).encode("utf-8"),
            ContentType="application/json"
        )
        print(f"Saved {filename} to MinIO")

        # add some logic here to generate interesting data for thingsboard

        channel.basic_publish(
            exchange='',
            routing_key=PROCESSED_QUEUE,
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )
        print(f"Published refined data to {PROCESSED_QUEUE}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=RAW_QUEUE, on_message_callback=callback)

print("Waiting for messages... Press CTRL+C to exit.")
channel.start_consuming()
