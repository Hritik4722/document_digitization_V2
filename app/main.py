from fastapi import FastAPI
from app.routes.upload import router as upload_img
app = FastAPI()

app.include_router(upload_img)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}