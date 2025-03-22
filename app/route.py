from app.core import app
from app.constants.paths import UPLOAD_FOLDER
from app.controllers.AskController import AskController

@app.route("/upload", methods=["POST"])
def upload ():
    return AskController.upload_pdf()

# API 2️⃣: Ajukan Pertanyaan dengan FAISS
@app.route("/ask", methods=["POST"])
def ask():
    return AskController.ask_question()

# API 3️⃣: Lihat Riwayat Interaksi
@app.route("/history", methods=["GET"])
def history():
    return AskController.get_history()

@app.route("/room/<pdf_id>")
def room(pdf_id):
    return AskController.get_room(pdf_id)

# API 4️⃣: Hapus Riwayat
@app.route("/clear-history", methods=["DELETE"])
def clear_history():
    return AskController.clear_history()

# Halaman Utama
@app.route('/')
def index():
    return AskController.index()
