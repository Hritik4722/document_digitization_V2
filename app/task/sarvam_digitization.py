from app.config import client
from app.services.job import update_job
from app.task.celery_config import celery
from app.services.storage import download_img_bytes, upload_img
# from io import BytesIO
import os

@celery.task
def process_img( key_path : str,lang:str , out_for: str, job_id :str,filename :str) -> str:
    output_path = f"uploads/{job_id}/output.zip"
    extension = os.path.splitext(filename)[1]
    temp_path = f"{job_id}{extension}"
    try:
        update_job(job_id,status="processing")
        #download image from r2
        image_bytes = download_img_bytes(key_path)
        if not image_bytes: 
            update_job(
                job_id,
                status="failed",
                error="Image not found"
            )
            return
        # file = BytesIO(image_bytes)
        with open(temp_path,"wb") as f:
            f.write(image_bytes)
        job = client.document_intelligence.create_job(
            language=lang,           # Target language (BCP-47 format)
            output_format=out_for         # Output format: "html" or "md" (delivered as ZIP)
        )
        job.upload_file(temp_path)
        job.start()
        status = job.wait_until_complete()
        print(f"Job {temp_path} completed: {status.job_state}")
        os.makedirs(f"uploads/{job_id}", exist_ok=True)
        
        job.download_output(f"./{output_path}")
        print("downloaded")
        with open(output_path,"rb") as f:
            upload_img(f.read(),output_path,"application/zip")

        update_job(job_id,status="completed", output_file= output_path)
        return {"status": "completed", "output_file": output_path}
    
    except Exception as e:
        update_job(
            job_id,
            status="failed",
            error=str(e)
        )
        raise
        

    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)