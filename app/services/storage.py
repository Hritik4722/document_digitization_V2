from dotenv import load_dotenv
import os
import boto3

load_dotenv()
r2 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id= os.getenv("R2_ACCESS_KEY"),
    aws_secret_access_key= os.getenv("R2_SECRET_KEY"),
    region_name= "auto"
)

def upload_img(data: bytes, path : str, content_type: str = "image/jpeg") -> bool:
    try:
        r2.put_object(
            Bucket = os.getenv("R2_BUCKET"),
            Key = path,
            Body = data,
            ContentType = content_type
        )
        return True
    except Exception as e:
        return False
    
def download_img_bytes(path :str) -> bytes:
    try:
        response = r2.get_object(
            Bucket = os.getenv("R2_BUCKET"),
            Key = path
        )

        data =  response["Body"].read()
        return data
    except Exception as e:
        return None
