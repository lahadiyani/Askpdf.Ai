// 🚩 Inisialisasi Elemen DOM
const uploadButton = document.getElementById('upload');
const fileInput = document.getElementById('file-upload');
const sendButton = document.getElementById('send-button');
const chatInput = document.getElementById('chat-input');
const chatContainer = document.getElementById('chat-container');
const typingIndicator = document.getElementById('typing-indicator');
const historyContainer = document.querySelector('.room-chat');

// 🚩 Fungsi Upload PDF
uploadButton.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async function () {
    if (this.files.length === 0) return alert('🚨 Harap pilih file PDF.');

    const file = this.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('https://askpdfai-production.up.railway.app/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            return alert(`❌ Upload gagal: ${data.error}`);
        }

        if (data.pdf_id) {
            localStorage.setItem('pdf_id', data.pdf_id);
            localStorage.setItem('filename', data.detected_title);
            alert('✅ PDF berhasil diunggah!');
            updateBookName();
            loadHistory();
        }
    } catch (error) {
        console.error('❌ Error:', error);
        alert('❗ Terjadi kesalahan saat mengunggah PDF.');
    }
});

// 🚩 Fungsi Kirim Pesan
async function sendMessage() {
    const message = chatInput.value.trim();
    const pdfId = localStorage.getItem('pdf_id');

    if (!message || !pdfId) {
        return alert('🚨 Harap unggah PDF terlebih dahulu!');
    }

    const formData = new FormData();
    formData.append('question', message);
    formData.append('pdf_id', pdfId);

    appendMessage('person', message);
    showTypingIndicator();

    try {
        const response = await fetch('https://askpdfai-production.up.railway.app/ask', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideTypingIndicator();

        if (data.answer?.trim()) {
            appendMessage('ai', formatMarkdown(data.answer));
        } else {
            appendMessage('ai', '⚠️ Maaf, saya tidak menemukan jawaban yang sesuai.');
        }
    } catch (error) {
        hideTypingIndicator();
        console.error('❌ Error:', error);
        appendMessage('ai', '❗ Terjadi kesalahan saat memproses data.');
    }

    chatInput.value = '';
    chatContainer.style.display = 'flex';
    loadHistory();
}

// 🚩 Event Listener untuk Tombol "Send"
sendButton.addEventListener('click', sendMessage);

// 🚩 Event Listener untuk "Enter" (Shift + Enter untuk newline)
chatInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

// 🚩 Fungsi Tambah Pesan ke Chat (Mencegah XSS)
function appendMessage(sender, message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'person' ? 'person-chat' : 'ai-chat';

    const sanitizedMessage = sanitizeHTML(sender === 'ai' ? formatMarkdown(message) : message);

    messageDiv.innerHTML = `
        <div class="message-bubble ${sender}-message">${sanitizedMessage}</div>
    `;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 🚩 Fungsi Sanitasi untuk Mencegah XSS
function sanitizeHTML(str) {
    const tempDiv = document.createElement('div');
    tempDiv.textContent = str;
    return tempDiv.innerHTML;
}

// 🚩 Fungsi Markdown Formatting
function formatMarkdown(text) {
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');  // **Bold**
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');  // *Italic*
    text = text.replace(/(^|\n)([A-Z][\w\s]+):/g, '<strong>$2:</strong>');  // Heading

    // Daftar Terurut (1. Item, 2. Item)
    text = text.replace(/(\d+\.\s.*(?:\n(?!\d+\.).*)*)/g, match => {
        const items = match.trim().split(/\n(?=\d+\.\s)/).map(item => item.replace(/^\d+\.\s(.*)/, '<li>$1</li>')).join('');
        return `<ol>${items}</ol>`;
    });

    // Daftar Tidak Terurut (- Item)
    text = text.replace(/(-\s.*(?:\n(?!- ).*)*)/g, match => {
        const items = match.trim().split(/\n(?=-\s)/).map(item => item.replace(/^- (.*)/, '<li>$1</li>')).join('');
        return `<ul>${items}</ul>`;
    });

    text = text.replace(/(?!<\/li>)\n/g, '<br>');  // Line Breaks

    return text.trim();
}

// 🚩 Indikator "Typing" untuk AI
function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// 🚩 Fungsi Load Riwayat Chat
async function loadHistory() {
    try {
        const response = await fetch('https://askpdfai-production.up.railway.app/history');
        const data = await response.json();

        if (!data.history || data.history.length === 0) {
            historyContainer.innerHTML = '<p>Belum ada riwayat chat.</p>';
            return;
        }

        historyContainer.innerHTML = ''; // Bersihkan sebelum render ulang
        historyContainer.style.display = 'flex';

        data.history.forEach(entry => {
            const historyItem = document.createElement('div');
            historyItem.classList.add('room');
            historyItem.dataset.pdfId = entry.id;

            historyItem.innerHTML = `
                <strong>📄 ${entry.question || 'Tidak Diketahui'}</strong><br>
                <small>🗓️ ${new Date(entry.timestamp).toLocaleString()}</small>
            `;

            historyItem.addEventListener('click', function () {
                window.location.href = `https://askpdfai-production.up.railway.app/room/${this.dataset.pdfId}`;
            });

            historyContainer.appendChild(historyItem);
        });

        historyContainer.scrollTop = historyContainer.scrollHeight;
    } catch (error) {
        console.error('❌ Gagal memuat riwayat:', error);
        historyContainer.innerHTML = '<p>⚠️ Gagal memuat riwayat chat.</p>';
    }
}

// 🚩 Fungsi Update Nama Buku
function updateBookName() {
    const bookNameElement = document.querySelector('.book-name');
    if (!bookNameElement) return; // Mencegah error jika elemen tidak ditemukan

    const filename = localStorage.getItem('filename');
    bookNameElement.textContent = filename || 'Nama Buku';
}

// 🚩 Event Listener Saat DOM Siap
document.addEventListener('DOMContentLoaded', updateBookName);
