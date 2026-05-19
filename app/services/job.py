import redis, json, os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis.from_url(os.getenv("REDIS_URL"),decode_response=True)

JOB_TTL = 43200

