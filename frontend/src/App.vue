<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="w-full max-w-4xl h-[80vh] bg-white shadow-xl rounded-xl flex flex-col">
      <header class="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-slate-800">
            DeepSeek Education Assistant
          </h1>
          <p class="text-sm text-slate-500">
            基于DeepSeek大语言模型的教育智能客服系统
          </p>
        </div>
        <span class="text-xs text-slate-400">
          WebSocket: ws://localhost:8000/ws/chat
        </span>
      </header>
      <main class="flex-1">
        <ChatBox />
      </main>
    </div>
  </div>
</template>

<script setup>
import ChatBox from './components/ChatBox.vue';
</script>

