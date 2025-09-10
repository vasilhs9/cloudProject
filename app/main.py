import json
import pika
import boto3
from datetime import datetime
from botocore.exceptions import ClientError


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

def save_weather_record_ndjson(data):
    date_str = datetime.utcnow().date().isoformat()
    filename = f"weather_{date_str}.json" #eather_2025-09-08.json

    data["timestamp"] = datetime.utcnow().isoformat()

    json_line = json.dumps(data)

    try:
        #get object content
        response = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
        existing = response["Body"].read().decode("utf-8")
        updated_content = existing + "\n" + json_line
    except s3.exceptions.NoSuchKey:
        #file doesn't exist yet
        updated_content = json_line

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=filename,
        Body=updated_content.encode("utf-8"),
        ContentType="application/json"
    )

    print(f"Appended record to {filename}")



def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode("utf-8"))

        # placeholder for processing data before saving
        temp = data.get("temperature")
        data["status"] = "good" if temp is not None and temp <= 25 else "bad"

        save_weather_record_ndjson(data)

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
