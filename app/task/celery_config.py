from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

celery = Celery(
    "document_ai",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
    include=["app.task.sarvam_digitization"]
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)