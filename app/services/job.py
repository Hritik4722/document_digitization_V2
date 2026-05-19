import redis, json, os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis.from_url(os.getenv("REDIS_URL"),decode_responses=True)

JOB_TTL = 43200

def create_job(job_id :str, filename : str, filepath : str):

    job = {
        "job_id":job_id,
        "filename" : filename,
        "input_file" : filepath,
        "output_file" : None,
        "status" : "queued",
        "created_at" : datetime.now().isoformat(),
        "error" : None
    }

    r.setex(job_id, JOB_TTL, json.dumps(job))
    return job

def get_job(job_id:str):
    data = r.get(job_id)
    if not data:
        return None
    
    return json.loads(data)

def update_job(job_id : str, **kwargs):
    job = get_job(job_id)
    if not job:
        return
    job.update(kwargs)
    r.setex(job_id,JOB_TTL,json.dumps(job))