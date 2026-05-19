# Document Digitization v2

This project is mainly about learning and applying worker-based background processing with Celery, Redis, and task queues.

The core idea is simple: the API accepts an image, puts the work into a queue, and a worker processes it in the background. That keeps the upload fast and separates the heavy document processing from the main request.

## Main Concept

I used this project to understand how these parts work together:

- FastAPI handles the upload request.
- Redis stores the queue and job state.
- Celery sends the work to a background worker.
- The worker processes the image asynchronously.
- The API later returns status and download links.

## How it works

1. `POST /upload` accepts an image plus `lang` and `output_format`.
2. The file is uploaded to R2 storage.
3. A Celery task is added to the Redis-backed queue.
4. A background worker picks up the task and processes the image.
5. You can check progress with `GET /status/{job_id}`.
6. When the job is done, `GET /download/{job_id}` returns a temporary download URL.

## What I learned

I learned how task queues help move slow work out of the main API flow. I also understood how Celery workers and Redis queues keep long-running jobs organized and reliable in a real project.

## Setup

Install dependencies:

```bash
pip install -r app/requirements.txt
```

Create a `.env` file with these values:

- `REDIS_URL`
- `R2_ENDPOINT`
- `R2_ACCESS_KEY`
- `R2_SECRET_KEY`
- `R2_BUCKET`
- `SARVAM_API_KEY`
- `OPENROUTER_API_KEY`

## Run

Start the API server:

```bash
uvicorn app.main:app --reload
```

Start the Celery worker in another terminal:

```bash
celery -A app.task.celery_config.celery worker --loglevel=info
```

## Use

Send a multipart form upload to `/upload` with:

- `file`: image file
- `lang`: target language
- `output_format`: `html` or `md`

Then use the returned `job_id` with `/status/{job_id}` and `/download/{job_id}`.