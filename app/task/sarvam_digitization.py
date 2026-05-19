from app.config import client
from app.services.job import update_job
from app.task.celery_config import celery
from app.services.storage import download_img_bytes, upload_img
from io import BytesIO
import os

@celery.task()
def process_img( key_path : str,lang:str , out_for: str, job_id :str) -> str:
    output_path = f"uploads/{job_id}/output.zip"
    try:
        update_job(job_id,status="processing")
        #download image from r2
        image_bytes = download_img_bytes(key_path)
        if not image_bytes: 
            return None
        file = BytesIO(image_bytes)

        job = client.document_intelligence.create_job(
            language=lang,           # Target language (BCP-47 format)
            output_format=out_for         # Output format: "html" or "md" (delivered as ZIP)
        )
        job.upload_file(file)
        job.start()
        status = job.wait_until_complete()

        os.makedirs(f"uploads/{job_id}", exist_ok=True)
        
        job.download_output(f"./{output_path}")

        with open(output_path,"rb") as f:
            upload_img(f.read(),output_path,"application/zip")

        update_job(job_id,status="completed", output_file= output_path)
        return {"status": "completed", "output_key": output_path}
    
    except Exception as e:
        print(e)
        

    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
    