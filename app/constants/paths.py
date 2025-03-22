import os

PATH_PROGRAM = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_FOLDER = f"/tmp/{PATH_PROGRAM}"
HISTORY_FILE = f"/tmp/{PATH_PROGRAM}-history.json"
ALLOWED_EXTENSIONS = ["pdf"]
