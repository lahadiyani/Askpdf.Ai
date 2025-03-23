import json
import os
from app.route import app  # Pastikan app.route ada `app = Flask(__name__)`
from app.constants.paths import UPLOAD_FOLDER, HISTORY_FILE

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    port = int(os.environ.get("PORT", 8080))  # Railway pakai PORT dari env

    # Inisialisasi file history jika belum ada
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)

    app.run(host='0.0.0.0', port=port)
