from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import uuid
from app.services.storage import upload_img
from app.services.job import create_job
from app.task.sarvam_digitization import process_img
router = APIRouter()

@router.post("/upload")
async def upload_img(file: UploadFile = File(...), lang : str = Form(...), output_format : str = Form(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    job_id = str(uuid.uuid4())

    content  = await file.read()
    key_filepath = f"uploads/{job_id}/{file.filename}" 
    #upload the image
    status = upload_img(content,key_filepath,file.content_type) #r2
    if(not status):
        raise HTTPException(status_code=500, detail="image Upload failed")
    
    #push a job in redis queue
    create_job(job_id,file.filename,key_filepath)

    #sneding task to the broker
    process_img.delay(key_filepath,lang, output_format,job_id)

    return{
        "job_id" : job_id,
        "status" : "queued"
    }


