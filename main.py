import json, os
from app import create_app
from app.constants.paths import UPLOAD_FOLDER, HISTORY_FILE

app = create_app()

if __name__=='__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Inisialisasi file history jika belum ada
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)

    app.run(debug=False, host='0.0.0.0', port=8000)
