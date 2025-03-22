from flask import Blueprint
from .constants.paths import UPLOAD_FOLDER
from .controllers.AskController import AskController

main = Blueprint("main", __name__)

@main.route("/upload", methods=["POST"])
def upload ():
    return AskController.upload_pdf()

# API 2️⃣: Ajukan Pertanyaan dengan FAISS
@main.route("/ask", methods=["POST"])
def ask():
    return AskController.ask_question()

# API 3️⃣: Lihat Riwayat Interaksi
@main.route("/history", methods=["GET"])
def history():
    return AskController.get_history()

@main.route("/room/<pdf_id>")
def room(pdf_id):
    return AskController.get_room(pdf_id)

# API 4️⃣: Hapus Riwayat
@main.route("/clear-history", methods=["DELETE"])
def clear_history():
    return AskController.clear_history()

# Halaman Utama
@main.route('/')
def index():
    return AskController.index()
