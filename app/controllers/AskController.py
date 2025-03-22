import json
import os
import io
from datetime import datetime
from flask import request, jsonify, render_template
from werkzeug.utils import secure_filename
from app.constants.paths import UPLOAD_FOLDER, HISTORY_FILE
from app.utils.functions import (
    generate_pdf_id, 
    is_contextual_question, 
    get_last_answer, 
    save_to_history
)
from app.lib.pdf.ai import ask_pollinations
from app.lib.pdf.pdfparser import (
    generate_embeddings,
    search_with_faiss,
    save_metadata_json,
    extract_intro_text  # Pastikan fungsi ini ada
)
import asyncio  # Untuk async function

class AskController:

    @staticmethod
    def index():
        return render_template('base.html')

    @staticmethod
    async def upload_pdf():
        if 'file' not in request.files:
            return jsonify({"error": "Tidak ada file yang diunggah"}), 400

        file = request.files['file']
        filename = secure_filename(file.filename)

        # 🔍 ID unik (tanpa file fisik)
        pdf_id = generate_pdf_id()

        # 📂 Baca file langsung di memori (tanpa simpan ke storage)
        file_stream = io.BytesIO(await asyncio.to_thread(file.read))

        # 🔍 Kirim ke AI dengan filename sebagai referensi
        prompt = (
            f"Aku Aseko, asisten AI yang ahli menganalisis PDF. "
            f"Coba tebak judul buku dari nama file ini secara lengkap: '{filename}'. "
            "Berikan jawaban singkat, hanya nama bukunya saja tanpa deskripsi tambahan."
        )
        book_title = await asyncio.to_thread(ask_pollinations, prompt)

        # 📖 Proses isi PDF langsung dari memory
        pdf_text = await asyncio.to_thread(extract_text_from_pdf, file_stream)

        # 📦 Buat metadata JSON tanpa menyimpan file
        metadata = {
            "pdf_id": pdf_id,
            "detected_title": book_title,
            "filename": filename,
            "text_preview": pdf_text[:500]  # Potong teks biar gak terlalu panjang
        }

        return jsonify(metadata), 200

    @staticmethod
    async def ask_question():
        question = request.form.get("question")
        pdf_id = request.form.get("pdf_id")
        top_k = request.form.get("top_k", 1)

        if not pdf_id or not question:
            return jsonify({"error": "ID PDF atau pertanyaan tidak boleh kosong."}), 400

        file_path = os.path.join(UPLOAD_FOLDER, f"{pdf_id}.pdf")
        if not os.path.exists(file_path):
            return jsonify({"error": "File PDF tidak ditemukan."}), 404

        try:
            top_k = int(top_k)
        except ValueError:
            return jsonify({"error": "Parameter top_k harus berupa angka."}), 400

        # 🔍 Cari teks paling relevan menggunakan FAISS
        relevant_text = await asyncio.to_thread(search_with_faiss, file_path, question, pdf_id, top_k)

        if isinstance(relevant_text, list) and "error" in relevant_text[0]:
            return jsonify({"error": relevant_text[0]["error"]}), 400

        # 🔗 Gunakan jawaban terakhir jika pertanyaan bersifat kontekstual
        last_answer = await asyncio.to_thread(get_last_answer, pdf_id)
        if is_contextual_question(question) and last_answer:
            context_prompt = (
                f"Berikut jawaban terakhir: '{last_answer}'. "
                "Jika ada pertanyaan seperti 'darimana kamu tahu' atau serupa, "
                "jawablah dengan sopan dan profesional. "
                "Jelaskan bahwa informasi tersebut diperoleh dari analisis dokumen tanpa menyebutkan detail sensitif."
            )
            prompt = f"Aku Aseko, asisten AI. {context_prompt} Jawab pertanyaan ini: '{question}'."
        else:
            prompt = (
                f"Aku Aseko, asisten AI yang ahli menganalisis dokumen PDF. "
                f"Berdasarkan hasil analisis isi PDF: {relevant_text}, jawab pertanyaan ini: '{question}'."
            )

        answer = await asyncio.to_thread(ask_pollinations, prompt)

        # Simpan ke riwayat
        await asyncio.to_thread(save_to_history, {
            "id": pdf_id,
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })

        return jsonify({
            "message": "Pertanyaan berhasil diproses!",
            "answer": answer,
            "pdf_id": pdf_id
        })

    @staticmethod
    async def get_history():
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        return jsonify({"history": history})

    @staticmethod
    async def get_room(pdf_id):
        file_path = os.path.join(UPLOAD_FOLDER, f"{pdf_id}.pdf")
        if not os.path.exists(file_path):
            return "PDF tidak ditemukan", 404

        return render_template("base.html", pdf_id=pdf_id)

    @staticmethod
    async def clear_history():
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)
        return jsonify({"message": "Riwayat berhasil dihapus!"})
