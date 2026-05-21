from bs4 import BeautifulSoup
from app.services.storage import upload_img
from app.task.celery_config import celery
from app.services.job import update_job
import zipfile, os, shutil

@celery.task
def merge_html(chunk_paths, job_id):
    try:
        chunk_paths.sort(
            key=lambda x: int(
                x.split("chunk_")[1]
                .split(".")[0]
            )
        )
        output_path = f"outputs/{job_id}/output.html"
        merged_body = ""
        styles = set()

        for path in chunk_paths:

            with zipfile.ZipFile(path) as z:

                html_name = next(
                    x for x in z.namelist()
                    if x.endswith(".html")
                )

                html = z.read(
                    html_name
                ).decode("utf-8")

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            # collect style blocks
            for style in soup.find_all("style"):
                styles.add(style.decode_contents())

            # collect page content
            if soup.body:
                merged_body += f"""
                <div class="page-break"></div>
                {soup.body.decode_contents()}
                """

        merged_css = "\n".join(styles)

        final_html = f"""
        <html>
        <head>

        <style>
        {merged_css}

        .page-break {{
            page-break-after: always;
        }}
        </style>

        </head>

        <body>
        {merged_body}
        </body>
        </html>
        """
        os.makedirs(f"outputs/{job_id}", exist_ok=True)
        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(final_html)

        with open(output_path,"rb") as f:
            upload_img(f.read(),f"uploads/{job_id}/output.html","text/html")


        update_job(job_id,status="completed", output_file= f"uploads/{job_id}/output.html")

    except Exception as e:
        update_job(job_id, status="failed", error=str(e))
        raise Exception("somethin went wrong")
    
    finally:
        pdf_folder = f"pdf/{job_id}"
        output_folder = f"outputs/{job_id}"

        if os.path.exists(pdf_folder):
            shutil.rmtree(pdf_folder)

        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)


    