from openai import OpenAI
from fastapi import HTTPException
from app.config import openrouter_client
from app.services.prompts import SYSTEM_PROMPT
import zipfile, os
from app.task.celery_config import celery
# First API call with reasoning

@celery.task
def cleanit(zip_file : str, chunk_id :int):

    try:
        if not os.path.exists(zip_file):
            raise HTTPException(404 ,"zip file not found")
        with zipfile.ZipFile(zip_file, "r") as zipf:
            html_content = zipf.read("document.html").decode("utf-8")
            # print(content.decode("utf-8"))
        print("---------------llm cleanup process")
        response = openrouter_client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324",
        messages=[
                {"role": "system","content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": html_content
                }
                ],
        extra_body={"reasoning": {"enabled": False}}
        )

        # Extract the assistant message with reasoning_details
        response = response.choices[0].message.content
        return {chunk_id : response}
        
    except Exception as e:
        print("llm went wrong :",e)
        raise