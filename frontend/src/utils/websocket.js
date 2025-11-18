let socket = null;
let listeners = new Set();

const WS_URL = 'ws://localhost:8000/ws/chat';

function setupSocket() {
  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    console.info('[WebSocket] Connected');
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      listeners.forEach((listener) => listener(data));
    } catch (error) {
      console.error('[WebSocket] Failed to parse message', error);
    }
  };

  socket.onclose = () => {
    console.warn('[WebSocket] Disconnected, attempting reconnect in 2s');
    setTimeout(() => {
      setupSocket();
    }, 2000);
  };

  socket.onerror = (event) => {
    console.error('[WebSocket] Error', event);
  };
}

export function initWebSocket() {
  if (!socket || socket.readyState === WebSocket.CLOSED) {
    setupSocket();
  }
}

export function addMessageListener(listener) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function sendUserMessage(payload) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    console.warn('[WebSocket] Not connected, cannot send message yet');
    return;
  }
  socket.send(JSON.stringify(payload));
}

