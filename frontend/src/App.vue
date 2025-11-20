<template>
  <div class="h-screen w-screen bg-[#E8ECF2] text-slate-900 grid grid-cols-[260px,1fr]">
    <!-- 左侧：会话导航，带交互功能 -->
    <aside class="bg-[#0F172A] text-slate-100 border-r border-slate-800/70 flex flex-col">
      <div class="p-4 border-b border-slate-800/70">
        <button
          type="button"
          class="w-full rounded-md bg-slate-100 text-slate-900 text-sm font-semibold py-2.5 flex items-center justify-center space-x-2 hover:bg-white transition"
          @click="createConversation"
        >
          <span class="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
          <span>新建对话</span>
        </button>
      </div>
      <div class="px-4 text-[11px] uppercase tracking-wide text-slate-400 mt-2">最近</div>
      <div class="flex-1 overflow-y-auto mt-2 space-y-1 px-2">
        <button
          v-for="item in histories"
          :key="item.id"
          class="w-full text-left px-3 py-3 rounded-md text-sm hover:bg-slate-800 transition flex flex-col space-y-1"
          :class="item.id === activeHistoryId ? 'bg-slate-800' : ''"
          @click="setActive(item.id)"
        >
          <span class="font-medium text-slate-100 truncate">{{ item.title }}</span>
          <span class="text-xs text-slate-400">{{ item.lastActive }} · {{ item.subject }}</span>
        </button>
      </div>
      <div class="p-4 border-t border-slate-800/70 text-xs text-slate-300 space-y-2">
        <div class="flex items-center space-x-2">
          <span class="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
          <span>ws://localhost:8000/ws/chat</span>
        </div>
        <div class="text-slate-500">DeepSeek RAG · Neo4j</div>
      </div>
    </aside>

    <!-- 右侧：主聊天区 -->
    <div class="grid grid-rows-[auto,1fr] bg-white shadow-inner">
      <header class="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="h-9 w-9 rounded-lg bg-[#1D4ED8] text-white flex items-center justify-center font-semibold text-sm shadow-blue-500/25 shadow-md">
            DS
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-900">DeepSeek 教育助手</p>
            <p class="text-xs text-slate-500">流式对话 · Markdown · ChatGPT 类排版</p>
          </div>
        </div>
        <div class="flex items-center space-x-2 text-xs text-slate-500">
          <span class="inline-flex items-center space-x-1">
            <span class="h-2 w-2 rounded-full bg-emerald-500" />
            <span>在线</span>
          </span>
          <span class="hidden sm:inline">/</span>
          <span class="hidden sm:inline">RAG + DeepSeek</span>
        </div>
      </header>

      <main class="flex-1 overflow-hidden bg-[#F8FAFC]">
        <ChatBox :conversation-id="activeHistoryId" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import ChatBox from './components/ChatBox.vue';

const histories = ref([
  { id: '1', title: '线性代数 · 矩阵入门', subject: '数学', lastActive: '今天' },
  { id: '2', title: '微积分 · 导数几何', subject: '数学', lastActive: '昨天' },
  { id: '3', title: '机器学习 · 监督学习', subject: 'AI', lastActive: '本周' },
  { id: '4', title: '物理 · 运动学', subject: '物理', lastActive: '本周' }
]);

const activeHistoryId = ref(histories.value[0]?.id ?? '');

function formatTimeLabel(date = new Date()) {
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

function createConversation() {
  const newId = `conv_${Date.now()}`;
  const label = formatTimeLabel();
  histories.value.unshift({
    id: newId,
    title: '新建对话',
    subject: '未分类',
    lastActive: label
  });
  activeHistoryId.value = newId;
}

function setActive(id) {
  const target = histories.value.find((item) => item.id === id);
  if (!target) return;
  target.lastActive = formatTimeLabel();
  activeHistoryId.value = id;
}
</script>
