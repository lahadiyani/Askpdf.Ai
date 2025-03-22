import os
import io

file_stream = io.BytesIO(file.read())

PATH_PROGRAM = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_FOLDER = f"/tmp/{PATH_PROGRAM}-storage"
HISTORY_FILE = f"/tmp/{PATH_PROGRAM}-history.json"
ALLOWED_EXTENSIONS = ["pdf"]
