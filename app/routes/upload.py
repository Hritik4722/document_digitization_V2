from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from io import BytesIO
import uuid
from PyPDF2 import PdfReader
from app.services.storage import upload_img, generate_down_url
from app.services.job import create_job, get_job, update_job
from app.task.sarvam_digitization import process_img
from app.task.pdf_sarvam_call import process_pdf
router = APIRouter()

@router.post("/upload")
async def upload_image(file: UploadFile = File(...), lang : str = Form(...), output_format : str = Form(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    job_id = str(uuid.uuid4())

    content  = await file.read()
    key_filepath = f"uploads/{job_id}/{file.filename}" 
    #upload the image
    status =upload_img(content,key_filepath,file.content_type) #r2
    if(not status):
        raise HTTPException(status_code=500, detail="image Upload failed")
    # print("uploaded to r2", status)
    #push a job in redis queue
    create_job(job_id,file.filename,key_filepath)

    #sneding task to the broker
    process_img.delay(key_filepath,lang, output_format,job_id,str(file.filename))

    return{
        "job_id" : job_id,
        "status" : "queued"
    }

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), lang: str = Form(...), output_format: str = Form(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400,"only pdf are allowed")
    job_id = str(uuid.uuid4())
    key_filepath = f"uploads/{job_id}/{file.filename}"

    try:
        create_job(job_id, file.filename, key_filepath)

        content = await file.read()
        reader = PdfReader(BytesIO(content))
        pdf_length = len(reader.pages)
        if pdf_length > 50:
            raise HTTPException(413, "only 50 page pdf allowed")
        
        status = upload_img(content, key_filepath, file.content_type)
        if not status:
            raise HTTPException(status_code=500, detail="file Upload failed")

        process_pdf.delay(key_filepath, lang, output_format, job_id, file.filename)

        return {
            "job_id": job_id,
            "status": "queued"
        }

    except HTTPException:
        update_job(job_id, status="failed", error="Invalid PDF upload request")
        raise
    except Exception as e:
        update_job(job_id, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail="PDF upload failed")


@router.get("/status/{job_id}")
async def status(job_id : str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return {
        "job_id": job["job_id"],
        "filename": job["filename"],
        "status": job["status"],        
        "created_at": job["created_at"],
        "error": job["error"]
    }

@router.get("/download/{job_id}")
def download(job_id : str):
    job = get_job(job_id)

    if not job:
        raise HTTPException(404, "job not found")
    
    if job["status"] != "completed":
        raise HTTPException(400 , f"job not ready. current status : {job['status']}")

    url = generate_down_url(job["output_file"], 3600)

    return{
        "job_id" : job_id,
        "download_url" : url,
        "expires_in" : "1 hours"
    }
