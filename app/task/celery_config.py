from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

celery = Celery(
    "document_ai",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
    include=["app.task.sarvam_digitization","app.task.pdf_sarvam_call","app.task.sarvam_call",
             "app.services.merge_chunks",
             "app.task.llm_cleanup"
             ]
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)