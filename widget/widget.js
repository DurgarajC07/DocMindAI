/**
 * DocMind AI - Embeddable Chat Widget
 * 
 * Usage:
 * <script src="https://yourdomain.com/widget.js" data-business-id="YOUR_BUSINESS_ID"></script>
 */

(function() {
    'use strict';

    // Get configuration from script tag
    const currentScript = document.currentScript;
    const businessId = currentScript.getAttribute('data-business-id');
    const apiBase = currentScript.getAttribute('data-api-base') || 'http://localhost:8000';
    
    if (!businessId) {
        console.error('DocMind AI: Missing data-business-id attribute');
        return;
    }

    let widgetConfig = {
        bot_name: 'AI Assistant',
        welcome_message: 'Hi! How can I help you today?',
        theme_color: '#4F46E5',
        api_endpoint: `${apiBase}/api/v1/chat/${businessId}`
    };

    let sessionId = localStorage.getItem(`docmind_session_${businessId}`) || generateUUID();
    localStorage.setItem(`docmind_session_${businessId}`, sessionId);

    // Utility function to generate UUID
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // Fetch widget configuration
    async function loadConfig() {
        try {
            const response = await fetch(`${apiBase}/api/v1/businesses/${businessId}/widget-config`);
            if (response.ok) {
                const config = await response.json();
                widgetConfig = { ...widgetConfig, ...config };
            }
        } catch (error) {
            console.warn('DocMind AI: Failed to load config, using defaults', error);
        }
    }

    // Create widget HTML
    function createWidget() {
        const widgetHTML = `
            <div id="docmind-widget" style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 999999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            ">
                <!-- Chat Button -->
                <button id="docmind-btn" aria-label="Open chat" style="
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: ${widgetConfig.theme_color};
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transition: transform 0.2s, box-shadow 0.2s;
                ">
                    <svg id="docmind-chat-icon" width="28" height="28" fill="white" viewBox="0 0 24 24">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                    </svg>
                    <svg id="docmind-close-icon" width="24" height="24" fill="white" viewBox="0 0 24 24" style="display: none;">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                </button>
                
                <!-- Chat Window -->
                <div id="docmind-chat" style="
                    display: none;
                    width: 370px;
                    height: 550px;
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 12px 48px rgba(0,0,0,0.2);
                    position: absolute;
                    bottom: 75px;
                    right: 0;
                    flex-direction: column;
                    overflow: hidden;
                ">
                    <!-- Header -->
                    <div style="
                        background: ${widgetConfig.theme_color};
                        padding: 20px;
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    ">
                        <div>
                            <h3 style="margin: 0; font-size: 18px; font-weight: 600;">${escapeHtml(widgetConfig.bot_name)}</h3>
                            <p style="margin: 4px 0 0; opacity: 0.9; font-size: 13px;">
                                We typically reply instantly
                            </p>
                        </div>
                        <div style="
                            width: 10px;
                            height: 10px;
                            background: #10b981;
                            border-radius: 50%;
                            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3);
                        "></div>
                    </div>
                    
                    <!-- Messages Container -->
                    <div id="docmind-messages" style="
                        flex: 1;
                        overflow-y: auto;
                        padding: 16px;
                        background: #f9fafb;
                    ">
                        <!-- Welcome Message -->
                        <div style="margin: 8px 0;">
                            <div style="
                                background: white;
                                padding: 12px 16px;
                                border-radius: 18px 18px 18px 4px;
                                display: inline-block;
                                max-width: 80%;
                                font-size: 14px;
                                line-height: 1.5;
                                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                            ">${escapeHtml(widgetConfig.welcome_message)}</div>
                        </div>
                    </div>
                    
                    <!-- Input Container -->
                    <div style="
                        padding: 16px;
                        border-top: 1px solid #e5e7eb;
                        background: white;
                        display: flex;
                        gap: 8px;
                        align-items: center;
                    ">
                        <input 
                            id="docmind-input" 
                            type="text" 
                            placeholder="Type your message..." 
                            style="
                                flex: 1;
                                padding: 10px 16px;
                                border: 1px solid #e5e7eb;
                                border-radius: 24px;
                                outline: none;
                                font-size: 14px;
                                font-family: inherit;
                            "
                        />
                        <button id="docmind-send-btn" aria-label="Send message" style="
                            background: ${widgetConfig.theme_color};
                            border: none;
                            color: white;
                            width: 40px;
                            height: 40px;
                            border-radius: 50%;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            transition: opacity 0.2s;
                        ">
                            <svg width="20" height="20" fill="white" viewBox="0 0 24 24">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </button>
                    </div>
                    
                    <!-- Powered By (for free tier) -->
                    <div style="
                        padding: 8px;
                        text-align: center;
                        font-size: 11px;
                        color: #9ca3af;
                        border-top: 1px solid #e5e7eb;
                    ">
                        Powered by <strong>DocMind AI</strong>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Toggle chat window
    function toggleChat() {
        const chat = document.getElementById('docmind-chat');
        const chatIcon = document.getElementById('docmind-chat-icon');
        const closeIcon = document.getElementById('docmind-close-icon');
        const btn = document.getElementById('docmind-btn');
        
        const isOpen = chat.style.display === 'flex';
        
        chat.style.display = isOpen ? 'none' : 'flex';
        chatIcon.style.display = isOpen ? 'block' : 'none';
        closeIcon.style.display = isOpen ? 'none' : 'block';
        btn.style.transform = isOpen ? 'scale(1)' : 'scale(0.95)';
        
        if (!isOpen) {
            document.getElementById('docmind-input').focus();
        }
    }

    // Add message to chat
    function addMessage(text, isUser = false) {
        const messages = document.getElementById('docmind-messages');
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `margin: 8px 0; text-align: ${isUser ? 'right' : 'left'};`;
        
        const bubble = document.createElement('div');
        bubble.style.cssText = `
            background: ${isUser ? widgetConfig.theme_color : 'white'};
            color: ${isUser ? 'white' : '#1f2937'};
            padding: 12px 16px;
            border-radius: ${isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px'};
            display: inline-block;
            max-width: 80%;
            font-size: 14px;
            line-height: 1.5;
            box-shadow: ${isUser ? '0 2px 8px rgba(79, 70, 229, 0.3)' : '0 1px 2px rgba(0,0,0,0.05)'};
            word-wrap: break-word;
        `;
        bubble.textContent = text;
        
        messageDiv.appendChild(bubble);
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    // Show typing indicator
    function showTyping() {
        const messages = document.getElementById('docmind-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'docmind-typing';
        typingDiv.style.cssText = 'margin: 8px 0;';
        
        typingDiv.innerHTML = `
            <div style="
                background: white;
                padding: 12px 16px;
                border-radius: 18px 18px 18px 4px;
                display: inline-block;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            ">
                <div style="display: flex; gap: 4px;">
                    <div style="width: 8px; height: 8px; background: #d1d5db; border-radius: 50%; animation: docmind-bounce 1.4s infinite ease-in-out both;"></div>
                    <div style="width: 8px; height: 8px; background: #d1d5db; border-radius: 50%; animation: docmind-bounce 1.4s infinite ease-in-out both; animation-delay: -0.32s;"></div>
                    <div style="width: 8px; height: 8px; background: #d1d5db; border-radius: 50%; animation: docmind-bounce 1.4s infinite ease-in-out both; animation-delay: -0.16s;"></div>
                </div>
            </div>
        `;
        
        messages.appendChild(typingDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    // Remove typing indicator
    function hideTyping() {
        const typing = document.getElementById('docmind-typing');
        if (typing) {
            typing.remove();
        }
    }

    // Send message
    async function sendMessage() {
        const input = document.getElementById('docmind-input');
        const question = input.value.trim();
        
        if (!question) return;
        
        // Add user message
        addMessage(question, true);
        input.value = '';
        input.disabled = true;
        
        // Show typing indicator
        showTyping();
        
        try {
            const response = await fetch(widgetConfig.api_endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    session_id: sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Remove typing indicator
            hideTyping();
            
            // Add bot response
            addMessage(data.answer, false);
            
        } catch (error) {
            console.error('DocMind AI: Failed to send message', error);
            hideTyping();
            addMessage('Sorry, something went wrong. Please try again.', false);
        } finally {
            input.disabled = false;
            input.focus();
        }
    }

    // Add animation styles
    const style = document.createElement('style');
    style.textContent = `
        @keyframes docmind-bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        #docmind-btn:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.2) !important;
        }
        
        #docmind-send-btn:hover {
            opacity: 0.9;
        }
        
        #docmind-input:focus {
            border-color: ${widgetConfig.theme_color};
            box-shadow: 0 0 0 3px ${widgetConfig.theme_color}22;
        }
        
        #docmind-messages::-webkit-scrollbar {
            width: 6px;
        }
        
        #docmind-messages::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        #docmind-messages::-webkit-scrollbar-thumb {
            background: #d1d5db;
            border-radius: 3px;
        }
        
        #docmind-messages::-webkit-scrollbar-thumb:hover {
            background: #9ca3af;
        }
    `;
    document.head.appendChild(style);

    // Initialize widget
    async function init() {
        await loadConfig();
        createWidget();
        
        // Add event listeners
        document.getElementById('docmind-btn').addEventListener('click', toggleChat);
        document.getElementById('docmind-send-btn').addEventListener('click', sendMessage);
        document.getElementById('docmind-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        console.log('DocMind AI Widget loaded successfully');
    }

    // Load widget when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
