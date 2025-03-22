import fitz
import json
import faiss
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import pdfplumber

vectorizer = TfidfVectorizer()
index = None
embedding_metadata = []

INDEX_PATH = "/tmp/faiss_index.bin"
METADATA_PATH = "/tmp/embedding_metadata.json"
VECTORIZER_PATH = "/tmp/vectorizer_vocab.json"

def extract_intro_text(file_path, max_chars=1000):
    try:
        with fitz.open(file_path) as pdf:
            if pdf.page_count > 0:
                text = pdf[0].get_text("text")
                return text[:max_chars] if text else "Teks tidak tersedia."
            return "PDF kosong."
    except Exception as e:
        print(f"Error saat mengekstrak teks: {e}")
        return "Gagal mengekstrak teks."

def extract_pdf_title(file_path):
    try:
        with fitz.open(file_path) as doc:
            title = doc.metadata.get('title')
            if not title or not title.strip():
                text = doc.load_page(0).get_text()
                title = text.split('\n')[0] if text else 'Dokumen Tanpa Judul'
            return title.strip()
    except Exception as e:
        print(f"Error mengambil judul: {e}")
        return "Dokumen Tanpa Judul"

def save_faiss_index():
    if index is not None:
        faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "w", encoding="utf-8") as meta_file:
        json.dump(embedding_metadata, meta_file, ensure_ascii=False, indent=4)
    with open(VECTORIZER_PATH, "w", encoding="utf-8") as vocab_file:
        json.dump(vectorizer.vocabulary_, vocab_file)

def load_faiss_index():
    global index, embedding_metadata, vectorizer
    if Path(INDEX_PATH).exists():
        index = faiss.read_index(INDEX_PATH)
    if Path(METADATA_PATH).exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as meta_file:
            embedding_metadata = json.load(meta_file)
    if Path(VECTORIZER_PATH).exists():
        with open(VECTORIZER_PATH, "r", encoding="utf-8") as vocab_file:
            vocab = json.load(vocab_file)
            vectorizer = TfidfVectorizer(vocabulary=vocab)
            if vocab:
                try:
                    vectorizer.fit(list(vocab.keys()))
                except ValueError:
                    vectorizer = TfidfVectorizer()
            else:
                vectorizer = TfidfVectorizer()

def generate_embeddings(pdf_path, pdf_id):
    global index, vectorizer
    base_folder = Path("/tmp") / pdf_id
    txt_folder = base_folder / "txt"
    json_folder = base_folder / "json"
    txt_folder.mkdir(parents=True, exist_ok=True)
    json_folder.mkdir(parents=True, exist_ok=True)

    all_texts = []
    with pdfplumber.open(pdf_path) as pdf:
        all_texts = [page.extract_text() for page in pdf.pages if page.extract_text()]
        all_texts = [text.strip() for text in all_texts if text]  # ✅ Tangani None

    if not all_texts:
        return

    vectorizer.fit(all_texts)
    vectors = vectorizer.transform(all_texts).toarray()

    if index is None or index.d != vectors.shape[1]:
        index = faiss.IndexFlatL2(vectors.shape[1])
        embedding_metadata.clear()

    index.add(np.array(vectors, dtype='float32'))

    for i, text in enumerate(all_texts):
        embedding_metadata.append({
            "doc_id": pdf_id,
            "page_number": i + 1,
            "text": text,
            "path": f"{Path(pdf_path).stem}.pdf"
        })

    save_faiss_index()
    save_metadata_json(pdf_id, pdf_path)

def save_metadata_json(pdf_id, pdf_path):
    json_folder = Path("/tmp") / pdf_id / "json"
    json_folder.mkdir(parents=True, exist_ok=True)
    metadata = {
        "id": pdf_id,
        "path": f"{Path(pdf_path).stem}.pdf",
        "name": Path(pdf_path).stem,
        "json_folder": str(json_folder)
    }
    with open(json_folder / "metadata.json", "w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, ensure_ascii=False, indent=4)

def search_with_faiss(pdf_path, query, pdf_id, top_k=3):
    global index, embedding_metadata, vectorizer
    load_faiss_index()  

    print(f"🔍 Pencarian untuk PDF ID: {pdf_id}, Query: '{query}'")

    metadata_path = Path(f"/tmp/{pdf_id}/json/metadata.json")  # ✅ Perbaiki path
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as file:
            pdf_metadata = json.load(file)
    else:
        print("⚠️ Metadata JSON tidak ditemukan.")
        return [{"error": "Metadata PDF tidak ditemukan."}]

    pdf_metadata = [meta for meta in embedding_metadata if meta["doc_id"] == pdf_id]

    if not pdf_metadata:
        print("⚠️ Tidak ada metadata untuk PDF ini.")
        return [{"error": "Tidak ada data untuk PDF ini."}]

    query_vector = vectorizer.transform([query]).toarray()[0]

    if index is None:
        print("🚨 FAISS Index belum dimuat!")
        return [{"error": "FAISS Index belum tersedia."}]

    if index.d != len(query_vector):
        print(f"⚠️ Dimensi tidak cocok: Index {index.d}, Query {len(query_vector)}")
        query_vector = np.array(query_vector, dtype='float32').reshape(1, -1)

    results = []
    if np.count_nonzero(query_vector) > 0:
        D, I = index.search(np.array([query_vector], dtype='float32'), top_k)
        for idx in I[0]:
            if 0 <= idx < len(pdf_metadata):
                results.append(pdf_metadata[idx])
    else:
        results = [meta for meta in pdf_metadata if query.lower() in meta["text"].lower()]

    return results if results else [{"error": "Tidak ditemukan hasil relevan."}]

def categorize_pdf_elements(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        all_texts = [page.extract_text() for page in pdf.pages if page.extract_text()]
        all_texts = [text.strip() for text in all_texts if text]  # ✅ Tangani None

    if not all_texts:
        return []

    vectors = vectorizer.transform(all_texts).toarray()
    kmeans = KMeans(n_clusters=5, random_state=42)
    labels = kmeans.fit_predict(vectors)

    return [{
        "page_number": idx + 1,
        "category": f"Cluster {label}",
        "text": all_texts[idx]
    } for idx, label in enumerate(labels)]
