"""Smoke test of the attachment tools. Downloads from the GAIA dataset and calls the Mistral API."""
import os

from gaia_agent.config import ATTACHMENTS_DIR
from gaia_agent.tools.files import (
    download_attachment,
    read_table_file,
    describe_image,
    transcribe_audio,
)

if __name__ == "__main__":
    print(download_attachment.invoke("7bd855d8-463d-4ed5-93ca-5fe35145f733"))
    print(read_table_file.invoke(os.path.join(ATTACHMENTS_DIR, "7bd855d8-463d-4ed5-93ca-5fe35145f733.xlsx")))
    print(download_attachment.invoke("99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3"))
    print(transcribe_audio.invoke(os.path.join(ATTACHMENTS_DIR, "99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3.mp3")))
    print(download_attachment.invoke("cca530fc-4052-43b2-b130-b30968d8aa44"))
    print(describe_image.invoke({
        "path": os.path.join(ATTACHMENTS_DIR, "cca530fc-4052-43b2-b130-b30968d8aa44.png"),
        "question": "What are the piece positions?",
    }))
    print(download_attachment.invoke("metadata"))
