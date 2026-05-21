from dotenv import load_dotenv
from app.config import client
from app.task.celery_config import celery
import os

load_dotenv()

@celery.task
def process_file(job_id: str, path :str,lang :str, out_format: str, chunk_id :int) -> str:
    output_path = f"outputs/{job_id}/chunk_{chunk_id}.zip"
    try:
        job = client.document_intelligence.create_job(
            language=lang,           # Target language (BCP-47 format)
            output_format=out_format         # Output format: "html" or "md" (delivered as ZIP)
        )
        job.upload_file(path)
        job.start()
        job.wait_until_complete()
        # print(f"Job {path} completed: {status.job_state}")
        os.makedirs(f"outputs/{job_id}", exist_ok=True)
        job.download_output(f"./{output_path}")
        return output_path
    
    except Exception as e:
        raise Exception(
            f"Chunk {chunk_id} failed: {str(e)}"
        )
    
    finally:
        if os.path.exists(path):
            os.remove(path)