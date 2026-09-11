// Client-side interactions for Mental Health Self-Help App

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Question Option Select Handling (Mental Test Screening Page)
    const optionBtns = document.querySelectorAll('.option-btn');
    optionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Find sibling buttons in the same question block and deselect them
            const questionBlock = this.closest('.question-block');
            questionBlock.querySelectorAll('.option-btn').forEach(b => {
                b.classList.remove('selected');
            });
            
            // Select this button
            this.classList.add('selected');
            
            // Check the internal radio input
            const radioInput = this.querySelector('input[type="radio"]');
            if (radioInput) {
                radioInput.checked = true;
            }
        });
    });

    // 2. Bookmark Toggle Handler (Article Education Page)
    const bookmarkBtns = document.querySelectorAll('.bookmark-toggle');
    bookmarkBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const articleId = this.dataset.articleId;
            const icon = this.querySelector('i');
            
            fetch(`/api/bookmark/${articleId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    if (data.bookmarked) {
                        icon.classList.remove('fa-regular');
                        icon.classList.add('fa-solid');
                        this.classList.add('active');
                    } else {
                        icon.classList.remove('fa-solid');
                        icon.classList.add('fa-regular');
                        this.classList.remove('active');
                    }
                } else {
                    alert('Gagal mengatur bookmark. Silakan login terlebih dahulu.');
                }
            })
            .catch(err => {
                console.error('Error toggling bookmark:', err);
            });
        });
    });

    // 3. Chatbot Core Logic
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    if (chatForm && chatInput && chatMessages) {
        // Scroll chat to bottom initially
        chatMessages.scrollTop = chatMessages.scrollHeight;

        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const messageText = chatInput.value.trim();
            if (!messageText) return;
            
            // Clear input
            chatInput.value = '';
            
            // Append User message bubble
            appendMessage('user', messageText);
            
            // Append typing indicator
            const typingId = showTypingIndicator();
            
            // Send request to Flask API
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText })
            })
            .then(res => res.json())
            .then(data => {
                // Remove typing indicator
                removeTypingIndicator(typingId);
                
                // Append Bot message bubble
                appendMessage('bot', data.reply, data.emotion, data.confidence, data.is_crisis, data.hotlines);
            })
            .catch(err => {
                console.error('Error sending message:', err);
                removeTypingIndicator(typingId);
                appendMessage('bot', 'Maaf, terjadi kesalahan koneksi. Silakan coba beberapa saat lagi.');
            });
        });
    }

    function appendMessage(sender, text, emotion = null, confidence = null, isCrisis = false, hotlines = null) {
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', sender);
        
        // Setup text with line breaks
        let contentHtml = `<div class="message-text">${text.replace(/\n/g, '<br>')}</div>`;
        
        // If emotion detected, add emotion tag
        if (sender === 'user' && emotion) {
            const percentage = Math.round(confidence * 100);
            const emoji = getEmotionEmoji(emotion);
            contentHtml += `<div class="emotion-tag">${emoji} ${emotion} (${percentage}%)</div>`;
        }
        
        // Append crisis card if emergency
        if (isCrisis) {
            contentHtml += `
                <div class="crisis-alert mt-3">
                    <h5><i class="fa-solid fa-triangle-exclamation"></i> Layanan Bantuan Darurat</h5>
                    <p class="mb-2">Jika Anda atau seseorang yang Anda kenal sedang mengalami krisis emosional, pikiran menyakiti diri sendiri, atau bunuh diri, silakan segera hubungi layanan profesional berikut:</p>
                    <ul class="mb-2 pl-3">
                        ${hotlines ? hotlines.map(h => `<li><strong>${h.name}</strong>: ${h.contact} (Tersedia ${h.address})</li>`).join('') : '<li><strong>Hotline Kemenkes</strong>: 119 Ext 9</li>'}
                    </ul>
                    <small>Ingat, Anda tidak sendirian. Ada pertolongan yang selalu siap membantu Anda.</small>
                </div>
            `;
        }
        
        // Add timestamp
        const time = new Date();
        const timestampStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        contentHtml += `<span class="timestamp">${timestampStr}</span>`;
        
        bubble.innerHTML = contentHtml;
        chatMessages.appendChild(bubble);
        
        // Auto scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', 'bot');
        bubble.id = id;
        
        bubble.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeTypingIndicator(id) {
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    }

    function getEmotionEmoji(emotion) {
        const emotionEmojis = {
            'Marah': '😠',
            'Kecewa': '😞',
            'Terlika': '😢',
            'Dendam': '😡',
            'Sakit hati': '💔',
            'Tersinggung': '😑',
            'Benci': '🤬',
            'Menyesal': '🥺',
            'Frustasi': '😩',
            'Takut': '😰',
            'Cemas': '😰',
            'Malu': '😳',
            'Kesepian': '👤',
            'Sedih': '😢',
            'Merasa tidak mampu': '😔',
            'Merasa putus asa': '😭',
            'Merasa tidak berharga': '🥀',
            'Merasa kecil': '🥺',
            'Merasa tidak di inginkan': '🖤',
            'Senang': '😊'
        };
        return emotionEmojis[emotion] || '😐';
    }
});
