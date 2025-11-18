<template>
  <div class="h-full flex flex-col">
    <div class="flex-1 overflow-y-auto px-6 py-4 space-y-4 bg-slate-50">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="flex"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[75%] rounded-xl px-4 py-2 text-sm leading-relaxed shadow-sm"
          :class="msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white text-slate-800 border border-slate-200'"
        >
          <div
            v-if="msg.role === 'assistant'"
            class="prose prose-sm max-w-none"
            v-html="renderMarkdown(msg.content || '')"
          />
          <p v-else>
            {{ msg.content }}
          </p>
        </div>
      </div>

      <div v-if="isTyping" class="flex items-center space-x-2 text-xs text-slate-500">
        <span class="w-2 h-2 rounded-full bg-slate-400 animate-pulse" />
        <span>Assistant is typing…</span>
      </div>
    </div>

    <form class="border-t border-slate-200 px-4 py-3 bg-white" @submit.prevent="handleSubmit">
      <div class="flex items-end space-x-2">
        <textarea
          v-model="inputText"
          rows="2"
          class="flex-1 resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="Ask a question about math, calculus, machine learning..."
          @keydown.enter.exact.prevent="handleSubmit"
        />
        <button
          type="submit"
          class="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium shadow hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!inputText.trim()"
        >
          Send
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, reactive, ref } from 'vue';
import { marked } from 'marked';
import { addMessageListener, initWebSocket, sendUserMessage } from '../utils/websocket';

const messages = reactive([]);
const inputText = ref('');
const isTyping = ref(false);

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
    return;
  }

  messages.push({
    id: chunk.message_id,
    role: 'assistant',
    content: chunk.content || '',
    isStreaming: !chunk.is_final
  });
  isTyping.value = !chunk.is_final;
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
}

let removeListener = null;

onMounted(() => {
  initWebSocket();
  removeListener = addMessageListener(handleAssistantChunk);
});

onBeforeUnmount(() => {
  if (removeListener) {
    removeListener();
  }
});
</script>

<style scoped>
.prose :where(p):not(:where([class~='not-prose'] *)) {
  margin: 0;
}
</style>

