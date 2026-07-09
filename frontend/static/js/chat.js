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

  function createMessageNode(msg) {
    // Build a message node that matches the chat CSS structure
    const el = document.createElement('div');
    const isUser = msg.role === 'user';
    el.className = 'message ' + (isUser ? 'user-message' : 'ai-message');

    // avatar
    const avatar = document.createElement('span');
    avatar.className = 'avatar';
    avatar.innerHTML = isUser ? 'You' : '<i class="fa-solid fa-wand-magic-sparkles"></i>';
    el.appendChild(avatar);

    // message content container
    const contentWrap = document.createElement('div');
    contentWrap.className = 'message-content';

    const p = document.createElement('p');
    p.textContent = msg.text;
    contentWrap.appendChild(p);

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
              <div class="messages" id="chatMessages" aria-live="polite"></div>
              <div class="chat-input">
                <textarea id="chatInput" placeholder="Ask about the uploaded PDFs... (Shift+Enter = newline)"></textarea>
                <div style="display:flex;flex-direction:column;gap:8px;">
                  <button id="chatSend">Ask</button>
                </div>
              </div>
            </div>

            <div class="chat-history-trigger-wrap">
              <button class="small-btn" id="chatHistoryToggle" type="button">History</button>
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
    const inputEl = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSend');
    const clearBtn = document.getElementById('chatClear');

    let messages = loadHistory();
    renderMessages(messagesEl, messages);
    buildHistorySidebar(messages);

    const historyToggleBtn = document.getElementById('chatHistoryToggle');
    const historySidebar = document.getElementById('chatHistorySidebar');
    historyToggleBtn?.addEventListener('click', () => {
      const willShow = historySidebar && historySidebar.hasAttribute('hidden');
      if (!historySidebar) return;
      if (willShow) {
        historySidebar.removeAttribute('hidden');
      } else {
        historySidebar.setAttribute('hidden', 'hidden');
      }
    });



    function appendAndSave(msg) {
      messages.push(msg);
      saveHistory(messages);
      renderMessages(messagesEl, messages);
      buildHistorySidebar(messages);
    }


    async function sendQuestion() {
      const q = (inputEl.value || '').trim();
      if (!q) return;
      inputEl.value = '';
      const userMsg = { role: 'user', text: q, ts: Date.now() };
      appendAndSave(userMsg);

      // Loading placeholder
      const stages = ['Searching PDFs...', 'Retrieving relevant pages...', 'Generating answer...'];
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
      const uploaded = window.uploadedPdfs || [];
      const pdf_ids = uploaded.map((f) => f.id);
      const askUrl = (window.pdfChatConfig && window.pdfChatConfig.askUrl) ? window.pdfChatConfig.askUrl : '/chat/ask';

      try {
        const resp = await fetch(askUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q, pdf_ids }),
        });
        const data = await resp.json();
        clearInterval(interval);
        // remove loading message
        messages.pop();
        if (resp.ok) {
          const aiMsg = { role: 'assistant', text: data.answer || 'No answer returned.', ts: Date.now() };
          appendAndSave(aiMsg);

        } else {
          const errMsg = { role: 'assistant', text: data.answer || data.error || 'Error from server.', ts: Date.now() };
          appendAndSave(errMsg);
        }
      } catch (err) {
        clearInterval(interval);
        messages.pop();
        appendAndSave({ role: 'assistant', text: 'Network error while contacting the server.', ts: Date.now() });
      }
    }

    sendBtn.addEventListener('click', sendQuestion);

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
