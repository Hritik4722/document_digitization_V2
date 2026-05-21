from app.config import client
from app.services.job import update_job
from app.task.celery_config import celery
from app.services.storage import download_img_bytes, upload_img
from PyPDF2 import PdfReader,PdfWriter
import os


@celery.task
def process_pdf( key_path : str,lang:str , out_for: str, job_id :str, filename :str) -> str:
    extension = os.path.splitext(filename)[1]
    temp_path = f"pdf/{job_id}/pdf_{job_id}.{extension}"
    update_job(job_id,status="processing")
    file_bytes = download_img_bytes(key_path)
    if not file_bytes: 
        update_job(
                job_id,
                status="failed",
                error="Image not found"
            )
        return
    # file = BytesIO(file_bytes)
    with open(temp_path,"wb") as f:
        f.write(file_bytes)

    #chunking the pdf
