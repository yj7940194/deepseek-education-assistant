<template>
  <div class="h-full flex flex-col bg-[#F9FAFB]">
    <div
      ref="scrollContainer"
      class="flex-1 overflow-y-auto px-6 py-6 space-y-5"
    >
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="flex"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          class="rounded-2xl px-5 py-4 text-[15px] leading-relaxed shadow-sm border border-slate-200 max-w-[80%]"
          :class="msg.role === 'user'
            ? 'bg-[#1D4ED8] text-white border-transparent'
            : 'bg-white text-slate-800'"
        >
          <template v-if="msg.role === 'assistant'">
            <div class="flex items-center text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
              <svg class="w-3.5 h-3.5 mr-2 text-[#2563EB]" viewBox="0 0 24 24" fill="none">
                <path
                  d="M5 3h14a2 2 0 0 1 2 2v16l-9-4-9 4V5a2 2 0 0 1 2-2z"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              来源：知识图谱
            </div>
            <div
              class="markdown-body text-[15px]"
              v-html="renderMarkdown(msg.content || '')"
            />
          </template>
          <template v-else>
            <p class="text-[15px]">
              {{ msg.content }}
            </p>
          </template>
        </div>
      </div>

      <div v-if="isTyping" class="flex items-center space-x-3 text-xs text-slate-500">
        <div class="typing-indicator">
          <span />
          <span />
          <span />
        </div>
        <span>助手正在思考知识图谱…</span>
      </div>
    </div>

    <form class="border-t border-slate-200/70 px-5 py-4 bg-white shadow-inner" @submit.prevent="handleSubmit">
      <div class="flex items-end space-x-3">
        <textarea
          v-model="inputText"
          rows="2"
          class="flex-1 resize-none rounded-2xl border border-slate-200 bg-white px-4 py-3 text-[15px] text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#93C5FD] focus:border-[#93C5FD]"
          placeholder="请提问数学、微积分、机器学习等领域的问题…"
          @keydown.enter.exact.prevent="handleSubmit"
        />
        <button
          type="submit"
          class="inline-flex items-center justify-center px-5 py-3 rounded-2xl bg-[#1D4ED8] text-white text-sm font-semibold shadow-lg shadow-blue-500/20 hover:bg-[#1E40AF] transition disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!inputText.trim()"
        >
          发送
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, reactive, ref, watch, nextTick } from 'vue';
import { marked } from 'marked';
import { addMessageListener, initWebSocket, sendUserMessage } from '../utils/websocket';

const messages = reactive([]);
const inputText = ref('');
const isTyping = ref(false);
const scrollContainer = ref(null);

function renderMarkdown(text) {
  return marked.parse(text || '');
}

function generateMessageId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `msg_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
}

function handleAssistantChunk(chunk) {
  if (chunk.type !== 'assistant_chunk') return;

  const existing = messages.find((m) => m.id === chunk.message_id && m.role === 'assistant');
  if (existing) {
    existing.content = (existing.content || '') + (chunk.content || '');
    if (chunk.is_final) {
      existing.isStreaming = false;
      isTyping.value = false;
    }
    queueScroll();
    return;
  }

  messages.push({
    id: chunk.message_id,
    role: 'assistant',
    content: chunk.content || '',
    isStreaming: !chunk.is_final
  });
  isTyping.value = !chunk.is_final;
  queueScroll();
}

function handleSubmit() {
  const text = inputText.value.trim();
  if (!text) return;

  const messageId = generateMessageId();

  messages.push({
    id: messageId,
    role: 'user',
    content: text
  });

  messages.push({
    id: messageId,
    role: 'assistant',
    content: '',
    isStreaming: true
  });

  isTyping.value = true;

  sendUserMessage({
    type: 'user_message',
    message_id: messageId,
    content: text,
    conversation_id: null
  });

  inputText.value = '';
  queueScroll();
}

function scrollToBottom(smooth = true) {
  const container = scrollContainer.value;
  if (!container) return;
  container.scrollTo({
    top: container.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto'
  });
}

function queueScroll() {
  requestAnimationFrame(() => {
    nextTick(() => scrollToBottom(true));
  });
}

let removeListener = null;

onMounted(() => {
  initWebSocket();
  removeListener = addMessageListener(handleAssistantChunk);
  queueScroll();
});

onBeforeUnmount(() => {
  if (removeListener) {
    removeListener();
  }
});

watch(
  () => messages.length,
  () => {
    queueScroll();
  }
);
</script>

<style scoped>
.markdown-body :deep(p) {
  margin: 0 0 1rem;
  color: #1f2937;
  line-height: 1.7;
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, monospace;
  background: #eff6ff;
  padding: 0.1rem 0.35rem;
  border-radius: 0.35rem;
  color: #1d4ed8;
}

.markdown-body :deep(pre) {
  background: #111827;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 0.75rem;
  overflow-x: auto;
  font-size: 0.9rem;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid #93c5fd;
  padding-left: 1rem;
  color: #475569;
  background: #f8fafc;
  border-radius: 0.5rem;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0 0 1rem 1.25rem;
  padding-left: 1.25rem;
}

.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.typing-indicator span {
  width: 0.45rem;
  height: 0.45rem;
  background: #94a3b8;
  border-radius: 999px;
  animation: typing-bounce 1s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.15s;
}
.typing-indicator span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typing-bounce {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  40% {
    transform: translateY(-0.2rem);
    opacity: 1;
  }
}
</style>
