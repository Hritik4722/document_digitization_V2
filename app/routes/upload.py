from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import uuid
from app.services.storage import upload_img
router = APIRouter()

@router.post("/upload")
async def upload_img(file: UploadFile = File(...), lang : str = Form(...), output_format : str = Form(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    job_id = str(uuid.uuid4())

    content  = await file.read()
    key_filepath = f"uploads/{job_id}/{file.filename}" 
    #upload the image
    status = upload_img(content,key_filepath,file.content_type)
    if(not status):
        raise HTTPException(status_code=500, detail="image Upload failed")
    
    #push a job in redis queue



