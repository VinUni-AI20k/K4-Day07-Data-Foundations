const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const historyList = document.querySelector("#history-list");
const retrievedProducts = document.querySelector("#retrieved-products");
const resultCount = document.querySelector("#result-count");
const metrics = document.querySelector("#metrics");
const retrieveWhere = document.querySelector("#retrieve-where");
const strategy = document.querySelector("#retrieval-strategy");
const runState = document.querySelector("#run-state");
const topK = document.querySelector("#top-k");
const originalQuery = document.querySelector("#original-query");
const rewrittenQuery = document.querySelector("#rewritten-query");
const activeTopK = document.querySelector("#active-top-k");
const guardrailStatus = document.querySelector("#guardrail-status");

let conversations = JSON.parse(localStorage.getItem("product-intelligence-chats") || "[]");
let activeId = null;

const escapeHtml = (value) => { const e = document.createElement("span"); e.textContent = value ?? ""; return e.innerHTML; };
const formatGbp = (value) => value == null ? "Price not stated" : new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format(value);
const formatCost = (value) => value == null ? "not configured" : `$${value.toFixed(6)}`;
const renderMarkdown = (text) => window.DOMPurify && window.marked ? DOMPurify.sanitize(marked.parse(text, { breaks: true, gfm: true })) : escapeHtml(text).replace(/\n/g, "<br>");

function save() { localStorage.setItem("product-intelligence-chats", JSON.stringify(conversations)); }
function activeChat() { return conversations.find((chat) => chat.id === activeId); }
function makeChat() { const chat = { id: crypto.randomUUID(), title: "Cuộc trò chuyện mới", messages: [] }; conversations.unshift(chat); activeId = chat.id; save(); return chat; }
function nearBottom() { return messages.scrollHeight - messages.scrollTop - messages.clientHeight < 110; }
function scrollMessages(force = false) { if (force || nearBottom()) messages.scrollTop = messages.scrollHeight; }

function renderHistory() {
  historyList.innerHTML = conversations.map((chat) => `<button class="history-item ${chat.id === activeId ? "active" : ""}" data-id="${chat.id}" type="button"><span>◻</span>${escapeHtml(chat.title)}</button>`).join("");
  historyList.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => { activeId = button.dataset.id; save(); render(); }));
}

function renderTrace(trace) {
  if (!trace.products.length) return `<section class="trace-card empty-trace"><strong>Retrieval result</strong><span>Không có product listing phù hợp trong corpus.</span></section>`;
  return `<section class="trace-card"><div class="trace-title"><strong>Retrieved context</strong><span>${trace.products.length} product listing</span></div>${trace.products.map((item) => `<div class="trace-row"><span class="trace-score">${item.score}</span><div><strong>${escapeHtml(item.name)}</strong><p>Matched: ${escapeHtml(item.matched_fields.join(", "))}</p><code>[${escapeHtml(item.citation.chunk_id)} | ${escapeHtml(item.citation.document_id)}]</code></div></div>`).join("")}</section>`;
}

function createMessage(role, content, trace = null) {
  const item = document.createElement("article");
  item.className = `message ${role}`;
  item.innerHTML = `<div class="avatar">${role === "user" ? "U" : "✦"}</div><div class="message-body"><p class="role-label">${role === "user" ? "YOU" : "PRODUCT INTELLIGENCE"}</p><div class="message-text ${role === "assistant" ? "markdown-body" : ""}"></div>${trace ? renderTrace(trace) : ""}</div>`;
  const textElement = item.querySelector(".message-text");
  if (role === "assistant") textElement.innerHTML = renderMarkdown(content);
  else textElement.textContent = content;
  messages.append(item);
  scrollMessages(true);
  return { item, textElement };
}

function welcomeMarkup() {
  return `<div class="welcome"><span class="welcome-icon">✦</span><h2>Tôi có thể tìm gì cho bạn?</h2><p>Hãy hỏi theo loại trang phục, thương hiệu, màu sắc hoặc đặc điểm. Câu trả lời chỉ dựa trên các product listing được truy xuất.</p><div class="prompt-grid"><button class="prompt" type="button">Tìm blazer màu trắng</button><button class="prompt" type="button">Gợi ý váy màu xanh</button><button class="prompt" type="button">Tôi cần áo Adidas</button></div></div>`;
}

function renderChat() {
  messages.innerHTML = "";
  const chat = activeChat();
  if (!chat || !chat.messages.length) { messages.innerHTML = welcomeMarkup(); attachPrompts(); return; }
  chat.messages.forEach((message) => createMessage(message.role, message.content, message.trace));
  scrollMessages(true);
}

function renderInspector() {
  const chat = activeChat();
  const last = [...(chat?.messages || [])].reverse().find((message) => message.metrics);
  if (!last) { resetInspector(); return; }
  updateInspector(last.metrics, last.trace.products);
}
function render() { renderHistory(); renderChat(); renderInspector(); }
function attachPrompts() { messages.querySelectorAll(".prompt").forEach((button) => button.addEventListener("click", () => { input.value = button.textContent; input.focus(); })); }

function updateInspector(data, products) {
  metrics.innerHTML = [["LATENCY", `${data.latency_ms} ms`], ["TOKENS", data.total_tokens || "not returned"], ["COST", formatCost(data.cost_usd)], ["RETRIEVED", data.retrieve_count]].map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`).join("");
  retrieveWhere.textContent = data.retrieve_where;
  strategy.textContent = data.retrieval_strategy;
  originalQuery.textContent = data.query || "—";
  rewrittenQuery.textContent = data.rewritten_query || "—";
  activeTopK.textContent = data.top_k ?? "—";
  guardrailStatus.textContent = data.guardrail || "—";
  resultCount.textContent = products.length;
  retrievedProducts.innerHTML = products.map((item) => `<article class="inspector-product"><div class="product-top"><span>${escapeHtml(item.category_group)}</span><b>score ${item.score}</b></div><h4>${escapeHtml(item.name)}</h4><p>${escapeHtml(item.brand)} · ${escapeHtml(item.color)}</p><strong>${formatGbp(item.price_gbp)}</strong><div class="tag-list">${item.matched_fields.map((field) => `<span>${escapeHtml(field)}</span>`).join("")}</div><code class="citation">[${escapeHtml(item.citation.chunk_id)} | ${escapeHtml(item.citation.document_id)}]</code><a href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">View source ↗</a></article>`).join("") || `<p class="empty-state">Không có product phù hợp.</p>`;
}
function resetInspector() { metrics.innerHTML = ["LATENCY", "TOKENS", "COST", "RETRIEVED"].map((label) => `<div class="metric"><span>${label}</span><strong>—</strong></div>`).join(""); retrieveWhere.textContent = "Chờ truy vấn đầu tiên"; strategy.textContent = "—"; originalQuery.textContent = "Chờ truy vấn đầu tiên"; rewrittenQuery.textContent = "—"; activeTopK.textContent = "—"; guardrailStatus.textContent = "—"; resultCount.textContent = "0"; retrievedProducts.innerHTML = `<p class="empty-state">Các product card sẽ hiện ở đây sau khi truy vấn.</p>`; runState.textContent = "Idle"; }

async function consumeSse(response, onEvent) {
  if (!response.ok || !response.body) throw new Error("Không thể mở luồng phản hồi.");
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    let boundary;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, boundary); buffer = buffer.slice(boundary + 2);
      const event = frame.match(/^event:\s*(.+)$/m)?.[1] || "message";
      const data = frame.match(/^data:\s*(.+)$/m)?.[1];
      if (data) onEvent(event, JSON.parse(data));
    }
    if (done) break;
  }
}

async function sendMessage(message) {
  if (!message.trim()) return;
  const chat = activeChat() || makeChat(); const priorHistory = chat.messages.slice(-6).map(({ role, content }) => ({ role, content }));
  if (chat.title === "Cuộc trò chuyện mới") chat.title = message.slice(0, 34);
  chat.messages.push({ role: "user", content: message }); save(); render(); input.value = ""; input.style.height = "auto";
  sendButton.disabled = true; runState.textContent = "Streaming"; runState.classList.add("running");
  const assistant = createMessage("assistant", ""); let output = ""; let trace = { products: [] }; let receivedDone = false; const selectedTopK = Number(topK.value);
  try {
    const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json", "Accept": "text/event-stream" }, body: JSON.stringify({ message, history: priorHistory, top_k: selectedTopK }) });
    await consumeSse(response, (event, data) => {
      if (event === "guardrail") { guardrailStatus.textContent = `${data.status}: ${data.reason}`; }
      if (event === "retrieval") { trace = { products: data.products }; assistant.item.querySelector(".message-body").insertAdjacentHTML("beforeend", renderTrace(trace)); updateInspector({ latency_ms: "…", total_tokens: "…", cost_usd: null, retrieve_count: trace.products.length, query: data.query, rewritten_query: data.rewritten_query, top_k: data.top_k, guardrail: "passed", retrieve_where: "data/k4_asos_products", retrieval_strategy: "weighted lexical metadata search" }, trace.products); }
      if (event === "delta") { const shouldStick = nearBottom(); output += data.text; assistant.textElement.innerHTML = renderMarkdown(output); if (shouldStick) scrollMessages(true); }
      if (event === "done") { chat.messages.push({ role: "assistant", content: output, trace, metrics: data.metrics }); save(); updateInspector(data.metrics, trace.products); runState.textContent = "Complete"; runState.classList.remove("running"); receivedDone = true; }
      if (event === "error") throw new Error(data.error);
    });
    if (!receivedDone) throw new Error("Luồng phản hồi kết thúc trước khi hoàn tất.");
  } catch (error) {
    assistant.textElement.textContent = `Không thể trả lời: ${error.message}`;
    chat.messages.push({ role: "assistant", content: `Không thể trả lời: ${error.message}` }); save(); runState.textContent = "Error"; runState.classList.remove("running");
  } finally { sendButton.disabled = false; renderHistory(); }
}

document.querySelector("#new-chat").addEventListener("click", () => { makeChat(); render(); input.focus(); });
form.addEventListener("submit", (event) => { event.preventDefault(); sendMessage(input.value); });
input.addEventListener("input", () => { input.style.height = "auto"; input.style.height = `${Math.min(input.scrollHeight, 150)}px`; });
if (!conversations.length) makeChat(); else activeId = conversations[0].id;
render();
