/* chat.js - modular frontend for PDF Chat UI
   - Stores chat history in sessionStorage
   - Sends single-question RAG requests to server (/chat/ask)
   - Shows loading animation, timestamps, copy and clear features
*/
(function () {
  const STORAGE_KEY = 'pdfChatHistory';

  function fmtTime(ts) {
    const d = new Date(ts);
    let hours = d.getHours();
    const minutes = d.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    return `${hours}:${minutes} ${ampm}`;
  }

    function loadHistory() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function buildHistorySidebar(history) {
    const historyBox = document.getElementById('chatHistoryBox');
    if (!historyBox) return;

    // Only show user questions
    const userMsgs = Array.isArray(history) ? history.filter((m) => m && m.role === 'user') : [];

    historyBox.innerHTML = '';
    if (!userMsgs.length) {
      historyBox.innerHTML = `
        <div class="history-empty">
          <i class="fa-regular fa-message"></i>
          <div class="history-empty-title">No questions yet</div>
          <div class="history-empty-sub">Ask something about your PDF.</div>
        </div>
      `;
      return;
    }

    // Render latest first
    userMsgs
      .slice()
      .reverse()
      .forEach((m, idx) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'history-item';
        item.title = m.text;
        item.textContent = m.text.length > 42 ? m.text.slice(0, 42) + '…' : m.text;
        item.addEventListener('click', () => {
          // Scroll to the corresponding question message
          const allMessageEls = document.querySelectorAll('#chatMessages .message');
          const targetUserIndex = history.lastIndexOf(m);
          // Best-effort: find the message with exact text
          const match = Array.from(allMessageEls).find((el) => {
            const p = el.querySelector('p');
            return p && p.textContent === m.text;
          });
          match?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
        historyBox.appendChild(item);
      });
  }


  function saveHistory(messages) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }

  function getUploadedPdfs() {
    return Array.isArray(window.uploadedPdfs) ? window.uploadedPdfs : [];
  }

  function appendInlineFormattedText(parent, text) {
    const parts = String(text || '').split(/(\*\*[^*]+\*\*)/g);
    parts.forEach((part) => {
      if (!part) return;
      if (part.startsWith('**') && part.endsWith('**')) {
        const strong = document.createElement('strong');
        strong.textContent = part.slice(2, -2).trim();
        parent.appendChild(strong);
        return;
      }
      parent.appendChild(document.createTextNode(part.replace(/\*\*/g, '')));
    });
  }

  function normalizeAnswerText(text) {
    return String(text || '')
      .replace(/\r\n?/g, '\n')
      .replace(/\s+(\d+)\.\s+/g, '\n$1. ')
      .replace(/\s+[*-]\s+/g, '\n- ')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  function isTableLine(line) {
    return /^\|.*\|$/.test(line.trim());
  }

  function isTableSeparator(line) {
    return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line.trim());
  }

  function parseTableRow(line) {
    return line
      .trim()
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((cell) => cell.trim());
  }

  function appendMarkdownTable(parent, tableLines) {
    const rows = tableLines.filter((line) => !isTableSeparator(line)).map(parseTableRow);
    if (!rows.length) return;

    const tableWrap = document.createElement('div');
    tableWrap.className = 'answer-table-wrap';
    const table = document.createElement('table');
    const header = document.createElement('thead');
    const headerRow = document.createElement('tr');

    rows[0].forEach((cell) => {
      const th = document.createElement('th');
      appendInlineFormattedText(th, cell);
      headerRow.appendChild(th);
    });
    header.appendChild(headerRow);
    table.appendChild(header);

    const body = document.createElement('tbody');
    rows.slice(1).forEach((row) => {
      const tr = document.createElement('tr');
      row.forEach((cell) => {
        const td = document.createElement('td');
        appendInlineFormattedText(td, cell);
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    table.appendChild(body);
    tableWrap.appendChild(table);
    parent.appendChild(tableWrap);
  }

  function normalizeSources(sources) {
    if (Array.isArray(sources)) {
      return sources.reduce((grouped, source) => {
        const filename = source.filename || 'unknown.pdf';
        const page = source.page || '?';
        grouped[filename] = grouped[filename] || new Set();
        grouped[filename].add(page);
        return grouped;
      }, {});
    }

    if (sources && typeof sources === 'object') {
      return Object.entries(sources).reduce((grouped, [filename, pages]) => {
        grouped[filename] = new Set(Array.isArray(pages) && pages.length ? pages : ['?']);
        return grouped;
      }, {});
    }

    return {};
  }

  function appendPageReferences(parent, sources) {
    const groupedSources = normalizeSources(sources);
    const entries = Object.entries(groupedSources);
    if (!entries.length) return;

    const refs = document.createElement('div');
    refs.className = 'page-references';
    const title = document.createElement('strong');
    title.textContent = 'Page references';
    refs.appendChild(title);

    entries.forEach(([filename, pages]) => {
      const row = document.createElement('div');
      row.className = 'page-reference-row';
      const sortedPages = Array.from(pages).sort((a, b) => Number(a) - Number(b));
      const file = document.createElement('span');
      file.className = 'page-reference-file';
      file.textContent = filename;
      const pageList = document.createElement('span');
      pageList.textContent = `Pages: ${sortedPages.join(', ')}`;
      row.appendChild(file);
      row.appendChild(pageList);
      refs.appendChild(row);
    });

    parent.appendChild(refs);
  }

  function appendFormattedAnswer(parent, text) {
    const lines = normalizeAnswerText(text).split('\n').map((line) => line.trim()).filter(Boolean);
    let activeList = null;
    let activeListType = '';

    function closeList() {
      activeList = null;
      activeListType = '';
    }

    function appendListItem(listType, content) {
      if (!activeList || activeListType !== listType) {
        activeList = document.createElement(listType);
        activeListType = listType;
        parent.appendChild(activeList);
      }
      const item = document.createElement('li');
      appendInlineFormattedText(item, content);
      activeList.appendChild(item);
    }

    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];
      if (isTableLine(line)) {
        closeList();
        const tableLines = [];
        while (index < lines.length && isTableLine(lines[index])) {
          tableLines.push(lines[index]);
          index += 1;
        }
        index -= 1;
        appendMarkdownTable(parent, tableLines);
        continue;
      }

      const numbered = line.match(/^(\d+)\.\s+(.*)$/);
      if (numbered) {
        appendListItem('ol', numbered[2]);
        continue;
      }

      const bullet = line.match(/^[-*]\s+(.*)$/);
      if (bullet) {
        appendListItem('ul', bullet[1]);
        continue;
      }

      closeList();
      const paragraph = document.createElement('p');
      appendInlineFormattedText(paragraph, line);
      parent.appendChild(paragraph);
    }

    if (!parent.childNodes.length) {
      const paragraph = document.createElement('p');
      paragraph.textContent = text || '';
      parent.appendChild(paragraph);
    }
  }

  function createMessageNode(msg) {
    // Build a message node that matches the chat CSS structure
    const el = document.createElement('div');
    const isUser = msg.role === 'user';
    el.className = 'message ' + (isUser ? 'user-message' : 'ai-message');
    if (msg.loading) {
      el.classList.add('loading-message');
    }

    // avatar
    const avatar = document.createElement('span');
    avatar.className = 'avatar';
    avatar.innerHTML = isUser ? 'You' : '<i class="fa-solid fa-wand-magic-sparkles"></i>';
    el.appendChild(avatar);

    // message content container
    const contentWrap = document.createElement('div');
    contentWrap.className = 'message-content';

    if (!isUser && msg.providerLabel) {
      const modelMeta = document.createElement('div');
      modelMeta.className = 'model-meta';
      modelMeta.textContent = `Using: ${msg.providerLabel}`;
      contentWrap.appendChild(modelMeta);
    }

    if (isUser) {
      const p = document.createElement('p');
      p.textContent = msg.text;
      contentWrap.appendChild(p);
    } else {
      const answer = document.createElement('div');
      answer.className = 'answer-content';
      appendFormattedAnswer(answer, msg.text);
      if (msg.loading) {
        const dots = document.createElement('span');
        dots.className = 'typing mini-typing';
        dots.innerHTML = '<span></span><span></span><span></span>';
        answer.appendChild(dots);
      }
      contentWrap.appendChild(answer);
      appendPageReferences(contentWrap, msg.sources);
    }

    // actions (copy, page badge, time)
    const actions = document.createElement('div');
    actions.className = 'message-actions';

    if (!isUser) {
      const copy = document.createElement('button');
      copy.className = 'copy-button';
      copy.title = 'Copy answer';
      copy.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
      copy.addEventListener('click', function () {
        navigator.clipboard.writeText(msg.text).then(() => {
          const old = copy.innerHTML;
          copy.textContent = 'Copied';
          setTimeout(() => (copy.innerHTML = old), 1200);
        });
      });
      actions.appendChild(copy);
    }

    // timestamp
    const time = document.createElement('span');
    time.className = 'message-time';
    time.textContent = fmtTime(msg.ts || Date.now());
    actions.appendChild(time);

    contentWrap.appendChild(actions);



    el.appendChild(contentWrap);
    return el;
  }

  function renderMessages(container, messages) {
    container.innerHTML = '';
    if (!messages.length) {
      const welcome = document.createElement('div');
      welcome.className = 'chat-welcome';
      welcome.innerHTML = `
        <i class="fa-regular fa-comments"></i>
        <h3>Welcome to SmartPDF AI</h3>
        <p>Upload your PDFs and start asking questions.</p>
      `;
      container.appendChild(welcome);
      return;
    }

    messages.forEach((m) => container.appendChild(createMessageNode(m)));
    // scroll to newest
    container.scrollTop = container.scrollHeight;
  }

  function makeLoadingMessage(text) {
    return { role: 'assistant', text: text, ts: Date.now(), loading: true };
  }

  document.addEventListener('DOMContentLoaded', function () {
    const chatPanel = document.querySelector('.llm-test-panel');
    if (!chatPanel) return;

    // Replace panel content with chat UI
    chatPanel.classList.add('pdf-chat-panel');
    chatPanel.innerHTML = `
      <div class="pdf-chat-header">
        <div class="pdf-chat-title">PDF Chat</div>
        <div class="controls">
          <button class="small-btn" id="chatClear">Clear Chat</button>
        </div>
      </div>

      <div class="pdf-chat-body">
        <div class="chat-window">
          <div class="chat-layout">
            <div class="chat-main">
              <div class="active-documents" id="activeDocuments" hidden></div>
              <div class="suggested-questions" id="suggestedQuestions" hidden></div>
              <div class="messages" id="chatMessages" aria-live="polite"></div>
              <label class="model-selector" for="aiModelSelect">
                <span>AI Model</span>
                <select id="aiModelSelect">
                  <option value="groq" selected>Groq Cloud</option>
                  <option value="ollama">Ollama Local</option>
                </select>
              </label>
              <div class="chat-input">
                <textarea id="chatInput" placeholder="Ask about the uploaded PDFs... (Shift+Enter = newline)"></textarea>
                <button id="chatSend" type="button">Ask</button>
              </div>
            </div>

            <div class="chat-history-trigger-wrap">
              <button class="small-btn" id="chatHistoryToggle" type="button" aria-expanded="false">History</button>
            </div>

            <aside class="chat-history-sidebar" aria-label="Chat history" id="chatHistorySidebar" hidden>

              <div class="chat-history-header">

                <span>History</span>
              </div>
              <div class="chat-history-box" id="chatHistoryBox"></div>
            </aside>
          </div>
        </div>
      </div>
    `;



    const messagesEl = document.getElementById('chatMessages');
    const activeDocumentsEl = document.getElementById('activeDocuments');
    const suggestedQuestionsEl = document.getElementById('suggestedQuestions');
    const inputEl = document.getElementById('chatInput');
    const modelSelect = document.getElementById('aiModelSelect');
    const sendBtn = document.getElementById('chatSend');
    const clearBtn = document.getElementById('chatClear');

    let messages = loadHistory();
    renderMessages(messagesEl, messages);
    buildHistorySidebar(messages);

    function renderActiveDocuments(files) {
      if (!activeDocumentsEl) return;
      activeDocumentsEl.innerHTML = '';
      if (!files.length) {
        activeDocumentsEl.hidden = true;
        return;
      }

      const title = document.createElement('span');
      title.className = 'active-documents-title';
      title.textContent = 'Active documents';
      activeDocumentsEl.appendChild(title);

      files.forEach((file) => {
        const item = document.createElement('span');
        item.className = 'active-document-pill';
        item.innerHTML = '<i class="fa-regular fa-file-pdf"></i>';
        item.appendChild(document.createTextNode(file.filename || 'PDF'));
        activeDocumentsEl.appendChild(item);
      });
      activeDocumentsEl.hidden = false;
    }

    function renderSuggestedQuestions(files) {
      if (!suggestedQuestionsEl) return;
      suggestedQuestionsEl.innerHTML = '';
      if (!files.length) {
        suggestedQuestionsEl.hidden = true;
        return;
      }

      const suggestions = [
        'Summarize this document',
        'Explain the main topic',
        'Create study notes',
        'What are the important concepts?',
      ];
      if (files.length === 2) {
        suggestions.push('Compare both PDFs');
      }

      const title = document.createElement('span');
      title.className = 'suggested-questions-title';
      title.textContent = 'Suggested questions';
      suggestedQuestionsEl.appendChild(title);

      const list = document.createElement('div');
      list.className = 'suggested-questions-list';
      suggestions.forEach((text) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = text;
        button.dataset.suggestedQuestion = text;
        list.appendChild(button);
      });
      suggestedQuestionsEl.appendChild(list);
      suggestedQuestionsEl.hidden = false;
    }

    function syncUploadedPdfUi() {
      const files = getUploadedPdfs();
      renderActiveDocuments(files);
      renderSuggestedQuestions(files);
    }

    syncUploadedPdfUi();

    const historyToggleBtn = document.getElementById('chatHistoryToggle');
    const historySidebar = document.getElementById('chatHistorySidebar');
    const chatLayout = document.querySelector('.chat-layout');
    historyToggleBtn?.addEventListener('click', () => {
      const willShow = historySidebar && historySidebar.hasAttribute('hidden');
      if (!historySidebar) return;
      if (willShow) {
        historySidebar.removeAttribute('hidden');
        chatLayout?.classList.add('history-open');
        historyToggleBtn.setAttribute('aria-expanded', 'true');
      } else {
        historySidebar.setAttribute('hidden', 'hidden');
        chatLayout?.classList.remove('history-open');
        historyToggleBtn.setAttribute('aria-expanded', 'false');
      }
    });



    function appendAndSave(msg) {
      messages.push(msg);
      saveHistory(messages);
      renderMessages(messagesEl, messages);
      buildHistorySidebar(messages);
    }


    async function sendQuestion(questionOverride) {
      const overrideText = typeof questionOverride === 'string' ? questionOverride : '';
      const q = (overrideText || inputEl.value || '').trim();
      if (!q) return;
      inputEl.value = '';
      const userMsg = { role: 'user', text: q, ts: Date.now() };
      appendAndSave(userMsg);

      // Loading placeholder
      const stages = ['Searching documents...', 'Finding relevant pages...', 'Generating answer...'];
      let stageIndex = 0;
      const loadingMsg = makeLoadingMessage(stages[stageIndex]);
      appendAndSave(loadingMsg);

      const interval = setInterval(() => {
        stageIndex = Math.min(stageIndex + 1, stages.length - 1);
        // update last message text
        messages[messages.length - 1].text = stages[stageIndex];
        saveHistory(messages);
        renderMessages(messagesEl, messages);
      }, 1200);

      // Build request
      const uploaded = getUploadedPdfs();
      const pdf_ids = uploaded.map((f) => f.id);
      const provider = modelSelect?.value || 'groq';
      const askUrl = (window.pdfChatConfig && window.pdfChatConfig.askUrl) ? window.pdfChatConfig.askUrl : '/chat/ask';

      try {
        const resp = await fetch(askUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q, pdf_ids, provider }),
        });
        const data = await resp.json();
        clearInterval(interval);
        // remove loading message
        messages.pop();
        if (resp.ok) {
          const aiMsg = {
            role: 'assistant',
            text: data.answer || 'No answer returned.',
            ts: Date.now(),
            provider: data.provider || provider,
            providerLabel: data.provider_label || (provider === 'ollama' ? 'Ollama Local' : 'Groq Cloud'),
            sources: data.sources || [],
          };
          appendAndSave(aiMsg);

        } else {
          const errMsg = {
            role: 'assistant',
            text: data.answer || data.error || 'Error from server.',
            ts: Date.now(),
            provider,
            providerLabel: provider === 'ollama' ? 'Ollama Local' : 'Groq Cloud',
          };
          appendAndSave(errMsg);
        }
      } catch (err) {
        clearInterval(interval);
        messages.pop();
        appendAndSave({
          role: 'assistant',
          text: 'Network error while contacting the server.',
          ts: Date.now(),
          provider,
          providerLabel: provider === 'ollama' ? 'Ollama Local' : 'Groq Cloud',
        });
      }
    }

    sendBtn.addEventListener('click', sendQuestion);

    suggestedQuestionsEl?.addEventListener('click', function (event) {
      const button = event.target.closest('[data-suggested-question]');
      if (!button) return;
      sendQuestion(button.dataset.suggestedQuestion || button.textContent || '');
    });

    // Wire example action buttons (e.g., "Summarize these PDFs") so clicking
    // them populates the input and immediately sends the question.
    const exampleBtns = document.querySelectorAll('.prompt-examples button');
    if (exampleBtns && exampleBtns.length) {
      exampleBtns.forEach((b) => {
        b.addEventListener('click', function () {
          const text = (this.textContent || '').trim();
          if (!text) return;
          inputEl.value = text;
          // small delay so UI updates before sending
          setTimeout(() => {
            sendQuestion();
          }, 50);
        });
      });
    }

    inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
      }
    });

    clearBtn.addEventListener('click', function () {
      if (!confirm('Clear chat history for this session?')) return;
      messages = [];
      saveHistory(messages);
      renderMessages(messagesEl, messages);
      buildHistorySidebar(messages);
    });

    document.addEventListener('pdfAiResponseMessage', function (event) {
      const detail = event.detail || {};
      appendAndSave({
        role: 'user',
        text: detail.userText || detail.prompt || 'Quick AI Action',
        ts: Date.now(),
      });
      appendAndSave({
        role: 'assistant',
        text: detail.answer || 'No response returned.',
        ts: Date.now(),
        provider: detail.provider || 'groq',
        providerLabel: detail.providerLabel || 'Groq Cloud',
        sources: detail.sources || [],
      });
    });

    document.addEventListener('pdfUploadsChanged', syncUploadedPdfUi);

  });
})();
// Creates a frontend-only AI chat preview with typing, copy, and history.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#chatForm");
    const input = document.querySelector("#questionInput");
    const messages = document.querySelector("#messages");
    const historyList = document.querySelector("#historyList");
    const clearHistory = document.querySelector("#clearHistory");
    const lastQuestion = document.querySelector("#infoLastQuestion");

    if (!form || !input || !messages) {
        return;
    }

    const dummyAnswers = [
        "This section appears to describe the main objective, supporting evidence, and expected outcome. Once backend AI is connected, this answer will be grounded in the uploaded PDF.",
        "A concise summary would include the problem statement, the proposed approach, and the metrics used to evaluate success.",
        "The most relevant detail is likely in the methodology or findings section. The final AI version can cite exact pages from retrieved chunks.",
    ];

    function scrollChat() {
        messages.scrollTop = messages.scrollHeight;
    }

    function createMessage(text, type, page) {
        const time = new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });
        const row = document.createElement("div");
        row.className = `message ${type}-message`;
        row.innerHTML = `
            <span class="avatar">${type === "user" ? "You" : '<i class="fa-solid fa-wand-magic-sparkles"></i>'}</span>
            <div class="message-content">
                <p></p>
                <div class="message-actions">
                    <button type="button" class="copy-button">
                        <i class="fa-regular fa-copy"></i>
                        Copy
                    </button>
                    <span class="page-badge">Page ${page}</span>
                    <span class="message-time">${time}</span>
                </div>
            </div>
        `;
        row.querySelector("p").textContent = text;
        row.querySelector(".copy-button").dataset.copy = text;
        messages.appendChild(row);
        scrollChat();
    }

    function addTyping() {
        const row = document.createElement("div");
        row.className = "message ai-message typing-row";
        row.innerHTML = `
            <span class="avatar"><i class="fa-solid fa-wand-magic-sparkles"></i></span>
            <div class="typing"><span></span><span></span><span></span></div>
        `;
        messages.appendChild(row);
        scrollChat();
        return row;
    }

    function addHistory(question) {
        if (!historyList) {
            return;
        }

        const empty = historyList.querySelector(".empty-state");
        if (empty) {
            empty.remove();
        }

        const item = document.createElement("div");
        item.className = "history-item";
        item.innerHTML = `
            <div>
                <strong></strong>
                <small>Just now</small>
            </div>
            <button class="delete-history" type="button" aria-label="Delete question">
                <i class="fa-solid fa-trash"></i>
            </button>
        `;
        item.querySelector("strong").textContent = question;
        historyList.prepend(item);
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const question = input.value.trim();

        if (!question) {
            window.showToast("Type a question first.");
            return;
        }

        createMessage(question, "user", "--");
        addHistory(question);
        if (lastQuestion) {
            lastQuestion.textContent = question;
        }
        input.value = "";

        const typing = addTyping();
        window.setTimeout(() => {
            typing.remove();
            const answer = dummyAnswers[Math.floor(Math.random() * dummyAnswers.length)];
            createMessage(answer, "ai", Math.floor(Math.random() * 24) + 1);
        }, 950);
    });

    messages.addEventListener("click", (event) => {
        const button = event.target.closest(".copy-button");
        if (!button) {
            return;
        }

        navigator.clipboard?.writeText(button.dataset.copy || "");
        window.showToast("Copied message.");
    });

    historyList?.addEventListener("click", (event) => {
        const button = event.target.closest(".delete-history");
        if (button) {
            button.closest(".history-item").remove();
            window.showToast("History item deleted.");
        }
    });

    clearHistory?.addEventListener("click", () => {
        if (historyList) {
            historyList.innerHTML = `
                <div class="history-item empty-state">
                    <i class="fa-regular fa-message"></i>
                    <span>No questions yet</span>
                    <small>Ask something about your PDF to build history.</small>
                </div>
            `;
        }
        window.showToast("History cleared.");
    });
});
