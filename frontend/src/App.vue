<template>
  <div class="h-screen w-screen bg-[#F3F4F6] text-slate-900">
    <div class="grid grid-rows-[auto,1fr] h-full">
      <header class="h-16 border-b border-slate-200 bg-white px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center space-x-4">
          <div class="h-10 w-10 rounded-xl bg-[#1D4ED8] text-white flex items-center justify-center font-semibold text-lg shadow-md shadow-blue-500/20">
            DS
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-900">DeepSeek 教学工作台</p>
            <p class="text-xs text-slate-500">Khanmigo 风格 · RAG + Neo4j · WebSocket 流式教学</p>
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <span class="text-xs text-slate-500 hidden sm:inline">
            WebSocket: ws://localhost:8000/ws/chat
          </span>
          <button
            type="button"
            class="inline-flex items-center space-x-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
            @click="toggleContext"
          >
            <span>{{ showContext ? '隐藏右侧面板' : '显示右侧面板' }}</span>
          </button>
          <div class="h-9 w-9 rounded-full bg-slate-200 border border-slate-300" aria-hidden="true" />
        </div>
      </header>

      <div
        class="grid h-full"
        :class="showContext ? 'grid-cols-[16rem,1fr,20rem]' : 'grid-cols-[16rem,1fr]'"
      >
        <!-- 左侧：会话与导航 -->
        <aside class="border-r border-slate-200 bg-white flex flex-col">
          <div class="px-4 py-3 border-b border-slate-200">
            <p class="text-sm font-semibold text-slate-800">会话记录</p>
            <p class="text-xs text-slate-500">复用历史对话或创建新会话</p>
          </div>
          <div class="flex-1 overflow-y-auto">
            <button
              v-for="item in histories"
              :key="item.id"
              class="w-full text-left px-4 py-3 border-b border-slate-100 hover:bg-slate-50 transition"
              :class="item.id === activeHistoryId ? 'bg-slate-100' : ''"
              @click="activeHistoryId = item.id"
            >
              <p class="text-sm font-semibold text-slate-800">{{ item.title }}</p>
              <p class="text-xs text-slate-500 mt-1">
                {{ item.subject }} · {{ item.lastActive }}
              </p>
            </button>
          </div>
          <div class="p-4 border-t border-slate-200">
            <button
              type="button"
              class="w-full rounded-xl bg-[#1D4ED8] text-white text-sm font-semibold py-2.5 shadow-md shadow-blue-500/25 hover:bg-[#1E40AF]"
            >
              新建会话
            </button>
          </div>
        </aside>

        <!-- 中间：主要聊天区域 -->
        <main class="bg-[#F9FAFB] flex flex-col">
          <div class="px-6 py-3 border-b border-slate-200 flex items-center justify-between">
            <div>
              <p class="text-sm font-semibold text-slate-800">对话工作区</p>
              <p class="text-xs text-slate-500">流式回答 · Markdown 渲染 · 思考指示</p>
            </div>
            <div class="flex items-center space-x-2 text-xs text-slate-500">
              <span class="inline-flex items-center space-x-1">
                <span class="h-2 w-2 rounded-full bg-emerald-500" />
                <span>实时连接</span>
              </span>
              <span class="hidden sm:inline">/</span>
              <span class="hidden sm:inline">RAG + DeepSeek</span>
            </div>
          </div>
          <div class="flex-1">
            <ChatBox />
          </div>
        </main>

        <!-- 右侧：上下文 / 知识图谱 -->
        <aside
          v-if="showContext"
          class="border-l border-slate-200 bg-white flex flex-col"
        >
          <div class="px-4 py-3 border-b border-slate-200">
            <p class="text-sm font-semibold text-slate-800">知识图谱上下文</p>
            <p class="text-xs text-slate-500">实时检索片段 / 来源标注</p>
          </div>
          <div class="flex-1 overflow-y-auto space-y-3 p-4">
            <article
              v-for="ctx in contextSnippets"
              :key="ctx.id"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
            >
              <p class="text-[13px] font-semibold text-slate-700 flex items-center space-x-2">
                <span class="h-2 w-2 rounded-full bg-[#2563EB]" aria-hidden="true" />
                <span>{{ ctx.topic }}</span>
              </p>
              <p class="text-xs text-slate-500 mt-1">{{ ctx.source }}</p>
              <p class="text-sm text-slate-800 mt-2 leading-relaxed">
                {{ ctx.snippet }}
              </p>
            </article>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import ChatBox from './components/ChatBox.vue';

const histories = ref([
  { id: '1', title: '线性代数 · 矩阵入门', subject: '数学', lastActive: '今天 14:20' },
  { id: '2', title: '微积分 · 导数几何意义', subject: '数学', lastActive: '昨天 20:35' },
  { id: '3', title: '机器学习 · 监督学习 vs 无监督', subject: 'AI', lastActive: '本周' },
  { id: '4', title: '物理 · 运动学基础', subject: '物理', lastActive: '本周' }
]);

const contextSnippets = ref([
  {
    id: 'c1',
    topic: '线性代数',
    source: '知识图谱 · Neo4j',
    snippet: '矩阵是按长方阵排列的数表，支持行列式、秩等运算，用于线性变换表示。'
  },
  {
    id: 'c2',
    topic: '微积分',
    source: '知识图谱 · Neo4j',
    snippet: '导数描述函数在某点的瞬时变化率，也可理解为切线斜率；常用极限定义或求导法则计算。'
  },
  {
    id: 'c3',
    topic: '机器学习',
    source: '知识图谱 · Neo4j',
    snippet: '监督学习通过带标签数据训练模型，最小化损失函数；常见算法包括线性回归、逻辑回归、SVM。'
  }
]);

const activeHistoryId = ref(histories.value[0]?.id ?? '');
const showContext = ref(true);

function toggleContext() {
  showContext.value = !showContext.value;
}
</script>
