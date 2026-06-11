class Chatbot {
    constructor(apiUrl, dashboardConfig = {}, tenantName = '') {
        this.apiUrl = apiUrl;
        this.dashboardConfig = dashboardConfig || {};
        this.tenantName = tenantName || 'home';
        this.currentConversationId = null;

        this.renderDashboard();
        this.bindCoreElements();
        this.loadPreferences();
    }

    responsePayload(resp) {
        if (resp && typeof resp === 'object' && resp.data && typeof resp.data === 'object') {
            return resp.data;
        }
        return resp || {};
    }

    responseSuccess(resp, httpOk = true) {
        if (resp && typeof resp.success === 'boolean') return resp.success;
        if (resp && typeof resp.status === 'string') return resp.status === 'success';
        if (resp && Object.prototype.hasOwnProperty.call(resp, 'error')) return false;
        return httpOk;
    }

    responseMessage(resp, fallback = '') {
        if (resp?.message?.text) return resp.message.text;
        if (typeof resp?.message === 'string') return resp.message;
        if (resp?.error) return resp.error;
        return fallback;
    }

    defaultDashboard() {
        return {
            version: 1,
            grid: { columns: 6, rows: 10 },
            modules: {
                collections: { type: 'collection_selector', enabled: true, placement: { col: 1, row: 1, colspan: 2, rowspan: 3 } },
                prompt: { type: 'prompt_editor', enabled: true, placement: { col: 1, row: 4, colspan: 2, rowspan: 2 } },
                conversations: { type: 'conversation_list', enabled: true, placement: { col: 1, row: 6, colspan: 2, rowspan: 5 } },
                chat: { type: 'chat', enabled: true, placement: { col: 3, row: 1, colspan: 4, rowspan: 10 } },
            },
        };
    }

    moduleElementId(moduleType) {
        return {
            'collection_selector': 'module-collection_selector',
            'prompt_editor': 'module-prompt_editor',
            'conversation_list': 'module-conversation_list',
            'chat': 'module-chat',
        }[moduleType] || null;
    }

    renderDashboard() {
        const dash = (this.dashboardConfig && this.dashboardConfig.modules) ? this.dashboardConfig : this.defaultDashboard();
        const grid = dash.grid || { columns: 6, rows: 10 };
        const container = document.getElementById('chatbot-dashboard');
        if (!container) return;
        container.innerHTML = '';
        container.style.setProperty('--dash-cols', String(Math.max(1, parseInt(grid.columns || 6, 10))));

        Object.keys(dash.modules || {}).forEach((moduleId) => {
            const conf = dash.modules[moduleId] || {};
            if (!conf.enabled) return;
            const elementId = this.moduleElementId(conf.type);
            const source = elementId ? document.getElementById(elementId) : null;
            if (!source) return;

            const card = source.cloneNode(true);
            card.id = `${elementId}-${moduleId}`;
            card.classList.remove('d-none');
            const p = conf.placement || {};
            card.style.gridColumn = `${Math.max(1, parseInt(p.col || 1, 10))} / span ${Math.max(1, parseInt(p.colspan || 1, 10))}`;
            card.style.gridRow = `${Math.max(1, parseInt(p.row || 1, 10))} / span ${Math.max(1, parseInt(p.rowspan || 1, 10))}`;
            container.appendChild(card);
        });
    }

    bindCoreElements() {
        this.chatForm = document.getElementById('chat-form');
        this.chatInput = document.getElementById('user-message');
        this.chatResponseDiv = document.getElementById('chat-response');
        this.newConversationBtn = document.getElementById('btn-new-conversation');
        this.clearConversationBtn = document.getElementById('btn-clear-conversation');
        this.collectionListDiv = document.getElementById('chatCollectionList');
        this.prepromptInput = document.getElementById('chat-user-preprompt');
        this.savePrefsBtn = document.getElementById('btn-save-chat-preferences');
        this.historyList = document.getElementById('chat-history-mini');

        if (this.chatForm) {
            this.chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }
        if (this.newConversationBtn) {
            this.newConversationBtn.addEventListener('click', () => this.startNewConversation());
        }
        if (this.clearConversationBtn) {
            this.clearConversationBtn.addEventListener('click', () => this.startNewConversation());
        }
        if (this.savePrefsBtn) {
            this.savePrefsBtn.addEventListener('click', () => this.savePreferences());
        }
    }

    async sendMessage() {
        if (!this.chatInput || !this.chatResponseDiv) return;
        const message = this.chatInput.value.trim();
        if (!message) return;
        this.appendMessage('user', message);
        this.chatInput.value = '';

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    selected_collections: this.getSelectedCollections(),
                    selected_groups: this.getSelectedGroups(),
                    conversation_id: this.currentConversationId,
                }),
            });
            const data = await response.json();
            const payload = this.responsePayload(data);
            if (!this.responseSuccess(data, response.ok)) {
                throw new Error(this.responseMessage(data, `HTTP ${response.status}`));
            }
            this.appendMessage('bot', payload.response, payload.sources || []);
            if (payload.conversation_id) {
                this.currentConversationId = payload.conversation_id;
            }
            if (Array.isArray(payload.conversations)) {
                this.renderConversations(payload.conversations, this.currentConversationId);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.appendMessage('bot', `Error: ${error.message || 'The chat request failed.'}`);
        }
    }

    appendMessage(sender, message, sources = []) {
        if (!this.chatResponseDiv) return;
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', sender);
        if (sender === 'bot') {
            messageDiv.innerHTML = this.formatBotMessage(message);
            if (Array.isArray(sources) && sources.length) {
                messageDiv.appendChild(this.buildSourcesBlock(sources));
            }
        } else {
            messageDiv.textContent = message;
        }
        this.chatResponseDiv.appendChild(messageDiv);
        this.chatResponseDiv.scrollTop = this.chatResponseDiv.scrollHeight;
    }

    formatBotMessage(message) {
        let safe = this.escapeHtml(message || '');
        safe = safe.replace(/\n{3,}/g, '\n\n');
        safe = safe.replace(/```([\s\S]*?)```/g, (_m, code) => `<pre class="chat-code"><code>${code.trim()}</code></pre>`);
        safe = safe.replace(/`([^`\n]+)`/g, '<code class="chat-inline-code">$1</code>');
        safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        safe = safe.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
        safe = safe.replace(/\n/g, '<br>');
        return safe;
    }

    buildSourcesBlock(sources) {
        const wrap = document.createElement('div');
        wrap.className = 'chat-sources mt-2';
        const title = document.createElement('div');
        title.className = 'chat-sources-title';
        title.textContent = 'Sources used:';
        wrap.appendChild(title);

        const list = document.createElement('ul');
        list.className = 'chat-sources-list';
        sources.forEach((src) => {
            const li = document.createElement('li');
            li.textContent = `${src?.label || ''}${src?.collection ? ` [${src.collection}]` : ''}`;
            list.appendChild(li);
        });
        wrap.appendChild(list);
        return wrap;
    }

    escapeHtml(text) {
        return (text || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    clearConversation() {
        if (!this.chatResponseDiv) return;
        this.chatResponseDiv.replaceChildren();
        if (this.chatInput) {
            this.chatInput.focus();
        }
    }

    async startNewConversation() {
        this.clearConversation();
        try {
            const response = await fetch('/chatbot/conversation/new', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            const payload = this.responsePayload(data);
            this.currentConversationId = payload.conversation_id || null;
            this.renderConversations(payload.conversations || [], this.currentConversationId);
        } catch (error) {
            console.error('Failed to start new conversation', error);
        }
    }

    async loadPreferences() {
        try {
            const response = await fetch('/chatbot/preferences', { method: 'GET' });
            if (!response.ok) return;
            const data = await response.json();
            const payload = this.responsePayload(data);
            this.renderCollections(payload.collections || [], payload.selected_collections || [], payload.collection_groups || [], payload.selected_groups || []);
            this.currentConversationId = null;
            this.renderConversations(payload.conversations || [], null);
            this.clearConversation();
            if (this.prepromptInput) {
                this.prepromptInput.value = payload.user_preprompt || '';
            }
        } catch (error) {
            console.error('Failed to load chat preferences', error);
        }
    }

    renderCollections(collections, selected, groups, selectedGroups) {
        if (!this.collectionListDiv) return;
        const selectedSet = new Set(selected || []);
        const selectedGroupSet = new Set(selectedGroups || []);
        this.collectionListDiv.innerHTML = '';

        (groups || []).forEach((item) => {
            const name = item.name;
            const checked = selectedGroupSet.has(name) ? 'checked' : '';
            const row = document.createElement('div');
            row.className = 'form-check';
            row.innerHTML = `<input class="form-check-input chat-group-checkbox" type="checkbox" id="chat-group-${name}" value="${name}" ${checked}><label class="form-check-label" for="chat-group-${name}">${item.label || name} (${item.count || 0})</label>`;
            this.collectionListDiv.appendChild(row);
        });

        if ((collections || []).length) {
            const details = document.createElement('details');
            details.className = 'mt-2';
            const summary = document.createElement('summary');
            summary.textContent = 'Advanced: select individual collections';
            details.appendChild(summary);
            const list = document.createElement('div');
            list.className = 'mt-2';
            (collections || []).forEach((item) => {
                const name = item.name;
                const checked = selectedSet.has(name) ? 'checked' : '';
                const row = document.createElement('div');
                row.className = 'form-check';
                row.innerHTML = `<input class="form-check-input chat-collection-checkbox" type="checkbox" id="chat-col-${name}" value="${name}" ${checked}><label class="form-check-label" for="chat-col-${name}">${name}</label>`;
                list.appendChild(row);
            });
            details.appendChild(list);
            this.collectionListDiv.appendChild(details);
        }
    }

    async savePreferences() {
        try {
            const response = await fetch('/chatbot/preferences', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    selected_collections: this.getSelectedCollections(),
                    selected_groups: this.getSelectedGroups(),
                    user_preprompt: this.prepromptInput ? this.prepromptInput.value.trim() : '',
                }),
            });
            const data = await response.json();
            if (!this.responseSuccess(data, response.ok)) {
                throw new Error(this.responseMessage(data, `HTTP ${response.status}`));
            }
            alert('Chat preferences saved.');
        } catch (error) {
            console.error('Failed to save chat preferences', error);
            alert('Failed to save chat preferences.');
        }
    }

    getSelectedCollections() {
        return Array.from(document.querySelectorAll('.chat-collection-checkbox:checked')).map((el) => el.value);
    }

    getSelectedGroups() {
        return Array.from(document.querySelectorAll('.chat-group-checkbox:checked')).map((el) => el.value);
    }

    renderConversations(conversations, currentId) {
        if (!this.historyList) return;
        this.historyList.innerHTML = '';
        (conversations || []).slice(0, 12).forEach((item) => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.style.cursor = 'pointer';
            const label = document.createElement('span');
            const title = item.title || 'Conversation';
            label.textContent = title.length > 48 ? `${title.slice(0, 48)}...` : title;
            if (item.id === currentId) label.classList.add('fw-bold');
            li.appendChild(label);

            const del = document.createElement('button');
            del.type = 'button';
            del.className = 'btn btn-sm btn-link text-danger p-0 chat-history-delete';
            del.title = 'Delete conversation';
            del.textContent = 'Delete';
            del.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.deleteConversation(item.id);
            });
            li.appendChild(del);

            li.addEventListener('click', () => this.selectConversation(item.id));
            this.historyList.appendChild(li);
        });
    }

    async deleteConversation(conversationId) {
        if (!conversationId) return;
        try {
            const response = await fetch('/chatbot/conversation/delete', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: conversationId }),
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            const payload = this.responsePayload(data);
            this.currentConversationId = payload.conversation_id || null;
            this.renderConversations(payload.conversations || [], this.currentConversationId);
            this.loadConversationHistory(payload.current_history || []);
        } catch (error) {
            console.error('Failed to delete conversation', error);
        }
    }

    async selectConversation(conversationId) {
        if (!conversationId) return;
        try {
            const response = await fetch('/chatbot/conversation/select', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: conversationId }),
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            const payload = this.responsePayload(data);
            this.currentConversationId = payload.conversation_id || conversationId;
            this.renderConversations(payload.conversations || [], this.currentConversationId);
            this.loadConversationHistory(payload.current_history || []);
        } catch (error) {
            console.error('Failed to select conversation', error);
        }
    }

    loadConversationHistory(history) {
        this.clearConversation();
        (history || []).forEach((turn) => {
            if (turn?.q) this.appendMessage('user', turn.q);
            if (turn?.a) this.appendMessage('bot', turn.a);
        });
    }
}
