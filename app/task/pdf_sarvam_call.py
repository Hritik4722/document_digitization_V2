from app.config import client
from app.services.job import update_job
from app.task.celery_config import celery
from app.task.sarvam_call import process_file
from app.services.merge_chunks import merge_html
from app.task.llm_cleanup import cleanit
from celery import chord, chain
from app.services.storage import download_img_bytes, upload_img
from PyPDF2 import PdfReader,PdfWriter
import os, math,shutil


@celery.task
def process_pdf( key_path : str,lang:str , out_for: str, job_id :str, filename :str) -> str:
    extension = os.path.splitext(filename)[1]
    temp_path = f"pdf/{job_id}/pdf_{job_id}{extension}"
    try:
        update_job(job_id, status="processing")
        file_bytes = download_img_bytes(key_path)
        if not file_bytes:
            update_job(
                job_id,
                status="failed",
                error="Image not found"
            )
            return

        os.makedirs(f"pdf/{job_id}", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        file_chunk_path = []
        reader = PdfReader(temp_path)
        pdf_length = len(reader.pages)
        if pdf_length > 10:
            curr_page = 0
            no_of_chunk = math.ceil(pdf_length / 10)

            for i in range(no_of_chunk):
                writer = PdfWriter()
                for page in (reader.pages[curr_page:curr_page + 10]):
                    writer.add_page(page)
                file_path = f"pdf/{job_id}/{curr_page}-{filename}"
                with open(file_path, "wb") as f:
                    writer.write(f)
                file_chunk_path.append(file_path)
                curr_page += 10
        else:
            file_chunk_path.append(temp_path)

        chord(
            chain(
                process_file.s(job_id, chunk, lang, out_for, i),
                cleanit.s(i)
            )for i, chunk in enumerate(file_chunk_path)
        )(
            merge_html.s(job_id)
        )

    except Exception as e:
        update_job(job_id, status="failed", error=str(e))
        raise




    

        
