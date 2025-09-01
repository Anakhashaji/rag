class ChatApp {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.chatMessages = document.getElementById('chatMessages');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.initializeBtn = document.getElementById('initializeBtn');
        this.clearChatBtn = document.getElementById('clearChatBtn');
        this.statusBtn = document.getElementById('statusBtn');
        this.statusIndicator = document.getElementById('statusIndicator');
        
        this.isProcessing = false;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        // Event listeners
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.initializeBtn.addEventListener('click', () => this.initializeSystem());
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
        this.statusBtn.addEventListener('click', () => this.checkStatus());
        
        // Example query clicks
        document.querySelectorAll('.example-query').forEach(element => {
            element.addEventListener('click', () => {
                const query = element.getAttribute('data-query');
                this.messageInput.value = query;
                if (this.isInitialized) {
                    this.sendMessage();
                }
            });
        });
        
        // Check initial status
        this.checkStatus();
    }
    
    async sendMessage() {
        if (this.isProcessing || !this.isInitialized) return;
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        this.isProcessing = true;
        this.updateUIState();
        
        // Add user message
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: message })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.addMessage(data.response, 'assistant', data.sources, data.metadata);
            } else {
                this.addMessage(`Error: ${data.error}`, 'assistant');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, I encountered an error processing your request. Please try again.', 'assistant');
        }
        
        this.isProcessing = false;
        this.updateUIState();
    }
    
    addMessage(content, sender, sources = null, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        let messageHTML = `
            <div class="message-content">
                <div class="message-header">
                    <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
                    <span class="sender">${sender === 'user' ? 'You' : 'RAG Assistant'}</span>
                </div>
                <div class="message-body">${this.formatMessage(content)}</div>
        `;
        
        // Add sources if available
        if (sources && sources.length > 0) {
            messageHTML += `
                <div class="message-sources">
                    <h6><i class="fas fa-link me-1"></i>Sources:</h6>
                    ${sources.map(source => this.formatSource(source)).join('')}
                </div>
            `;
        }
        
        // Add metadata if available
        if (metadata && Object.keys(metadata).length > 0) {
            messageHTML += `
                <div class="message-metadata mt-2">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Found ${metadata.relevant_count || 0} relevant results
                        ${metadata.filters_applied && Object.keys(metadata.filters_applied).length > 0 ? 
                            ` (filters: ${Object.keys(metadata.filters_applied).join(', ')})` : ''}
                    </small>
                </div>
            `;
        }
        
        messageHTML += '</div>';
        messageDiv.innerHTML = messageHTML;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // Simple formatting for line breaks and basic markdown
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    formatSource(source) {
        return `
            <div class="source-item">
                <div><strong>Feedback by:</strong> ${source.feedback_id}</div>
                <div class="source-meta">
                    ${source.project ? `<span class="source-tag">Project: ${source.project}</span>` : ''}
                    ${source.course ? `<span class="source-tag">Course: ${source.course}</span>` : ''}
                    ${source.centre ? `<span class="source-tag">Centre: ${source.centre}</span>` : ''}
                    ${source.batch ? `<span class="source-tag">Batch: ${source.batch}</span>` : ''}
                    ${source.date ? `<span class="source-tag">Date: ${source.date}</span>` : ''}
                    ${source.trainer ? `<span class="source-tag">Trainer: ${source.trainer}</span>` : ''}
                    ${source.logged_by ? `<span class="source-tag">Logged by: ${source.logged_by}</span>` : ''}
                </div>
                <div class="mt-2">
                    <small><strong>Content Types:</strong> ${source.content_types.join(', ')}</small>
                    <small class="float-end"><strong>Relevance:</strong> ${(source.relevance_score * 100).toFixed(1)}%</small>
                </div>
            </div>
        `;
    }
    
    async initializeSystem() {
        this.initializeBtn.disabled = true;
        this.initializeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Initializing...';
        
        try {
            const response = await fetch('/api/initialize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.isInitialized = true;
                this.updateStatus('ready', 'System Ready');
                this.addMessage(`System initialized successfully! ${data.message}`, 'assistant');
                this.updateUIState();
            } else {
                this.addMessage(`Initialization failed: ${data.error}`, 'assistant');
                this.updateStatus('error', 'Initialization Failed');
            }
        } catch (error) {
            console.error('Error initializing system:', error);
            this.addMessage('Failed to initialize system. Please check the console for details.', 'assistant');
            this.updateStatus('error', 'Connection Error');
        }
        
        this.initializeBtn.disabled = false;
        this.initializeBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Initialize System';
    }
    
    async checkStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (response.ok) {
                this.isInitialized = data.initialized;
                
                if (data.initialized) {
                    this.updateStatus('ready', `Ready (${data.vector_store.total_chunks || 0} chunks)`);
                } else {
                    this.updateStatus('warning', 'Not Initialized');
                }
                
                this.updateUIState();
            } else {
                this.updateStatus('error', 'Status Check Failed');
            }
        } catch (error) {
            console.error('Error checking status:', error);
            this.updateStatus('error', 'Connection Error');
        }
    }
    
    updateStatus(type, text) {
        const iconClass = {
            'ready': 'fas fa-circle text-success',
            'warning': 'fas fa-circle text-warning',
            'error': 'fas fa-circle text-danger',
            'loading': 'fas fa-spinner fa-spin text-info'
        }[type] || 'fas fa-circle text-warning';
        
        this.statusIndicator.innerHTML = `
            <i class="${iconClass}"></i>
            <span class="status-text">${text}</span>
        `;
    }
    
    updateUIState() {
        this.messageInput.disabled = this.isProcessing || !this.isInitialized;
        this.sendBtn.disabled = this.isProcessing || !this.isInitialized;
        
        if (this.isProcessing) {
            this.loadingIndicator.style.display = 'block';
            this.sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        } else {
            this.loadingIndicator.style.display = 'none';
            this.sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }
    
    clearChat() {
        // Keep only the welcome message
        const welcomeMessage = this.chatMessages.querySelector('.assistant-message');
        this.chatMessages.innerHTML = '';
        if (welcomeMessage) {
            this.chatMessages.appendChild(welcomeMessage);
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});