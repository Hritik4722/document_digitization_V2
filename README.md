# Document Digitization v2

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square)
![Celery](https://img.shields.io/badge/Celery-5.x-brightgreen?style=flat-square)
![Redis](https://img.shields.io/badge/Redis-7.x-red?style=flat-square)
![Cloudflare R2](https://img.shields.io/badge/Cloudflare-R2-orange?style=flat-square)

This project is mainly about learning and applying worker-based background processing with Celery, Redis, and task queues.

A document digitization API that accepts an image, extracts and digitizes its content using the Sarvam AI API, and returns a downloadable output — all processed asynchronously in the background.

The core idea is simple: the API accepts an image, puts the work into a queue, and a worker processes it in the background. That keeps the upload fast and separates the heavy document processing from the main request.

## Main Concept

I used this project to understand how these parts work together:

- FastAPI handles the upload request.
- Redis stores the queue and job state.
- Celery sends the work to a background worker.
- The worker processes the image asynchronously.
- The API later returns status and download links.


## Architecture

```
POST /upload
     │
     ▼
  FastAPI  ──── upload original ────▶  Cloudflare R2
     │                                      │
     │ push task                            │
     ▼                                      │
   Redis                                    │
  (queue)                                   │
     │                                      │
     │ pick up task                         │
     ▼                                      ▼
Celery Worker ◀──── download file ──── Cloudflare R2
     │
     │ send to Sarvam AI
     ▼
 Sarvam API
(Document Digitization)
     │
     │ upload result
     ▼
Cloudflare R2
     │
     │ presigned URL
     ▼
GET /download/{job_id}
```

## Stack

| Layer | Tool |
|---|---|
| API | FastAPI |
| Background jobs | Celery |
| Queue & job store | Redis |
| File storage | Cloudflare R2 |
| OCR / Digitization | Sarvam AI |
| LLM cleanup | OpenRouter |

## How it works

1. `POST /upload` accepts an image with `lang` and `output_format`
2. The file is uploaded to Cloudflare R2
3. A Celery task is pushed to the Redis-backed queue
4. A background worker picks up the task — no waiting on the API side
5. The worker sends the image to Sarvam AI for digitization
6. The result is uploaded back to R2
7. `GET /status/{job_id}` lets you poll for progress
8. `GET /download/{job_id}` returns a temporary presigned URL when done

## Setup

**1. Install dependencies**
```bash
pip install -r app/requirements.txt
```

**2. Create a `.env` file**
```env
REDIS_URL=redis://localhost:6379
R2_ENDPOINT=https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
R2_ACCESS_KEY=your_access_key
R2_SECRET_KEY=your_secret_key
R2_BUCKET=your_bucket_name
SARVAM_API_KEY=your_sarvam_key
OPENROUTER_API_KEY=your_openrouter_key
```

**3. Start Redis**
```bash
docker run -p 6379:6379 redis:alpine
```

## Run

**Terminal 1 — API server**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 — Celery worker**
```bash
celery -A app.task.celery_config.celery worker --loglevel=info
```

API docs available at `http://localhost:8000/docs`

## API Reference

### `POST /upload`
Upload an image for digitization.

| Field | Type | Description |
|---|---|---|
| `file` | image file | The document image |
| `lang` | string | Target language (e.g. `en-IN`, `hi-IN`) |
| `output_format` | string | `html` or `md` |

**Response**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

---

### `GET /status/{job_id}`
Poll for job progress.

**Response**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "filename": "document.jpg"
}
```

Status values: `queued` → `processing` → `completed` / `failed`

---

### `GET /download/{job_id}`
Get a presigned download URL (valid 1 hour).

**Response**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "download_url": "https://...",
  "expires_in": "1 hour"
}
```

## Example (curl)

```bash
# upload
curl -X POST http://localhost:8000/upload \
  -F "file=@document.jpg" \
  -F "lang=en-IN" \
  -F "output_format=html"

# check status
curl http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000

# download when completed
curl http://localhost:8000/download/550e8400-e29b-41d4-a716-446655440000
```

## What I learned

- How task queues decouple slow work from the main API request cycle
- How Celery workers and Redis queues keep long-running jobs organized
- How Cloudflare R2 works as S3-compatible object storage using `boto3`
- How presigned URLs let users download files directly from storage
- How to structure a FastAPI project with background processing
