import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getConversations, getUnreadCount } from '../api/modules'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const unreadTotal = ref(0)
  const currentConversation = ref(null)
  const ws = ref(null)

  async function fetchConversations() {
    const res = await getConversations()
    conversations.value = res.data.results || res.data
  }

  async function fetchUnreadCount() {
    const res = await getUnreadCount()
    unreadTotal.value = res.data.unread_count
  }

  function connectWebSocket(conversationId, token, onMessage) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/chat/${conversationId}/?token=${token}`

    if (ws.value) {
      ws.value.close()
    }

    ws.value = new WebSocket(wsUrl)
    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (onMessage) onMessage(data)
    }
    ws.value.onclose = () => {
      console.log('WebSocket disconnected')
    }
    ws.value.onerror = (err) => {
      console.error('WebSocket error:', err)
    }
  }

  function sendWsMessage(content) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ type: 'message', content }))
    }
  }

  function disconnectWebSocket() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  return {
    conversations, unreadTotal, currentConversation,
    fetchConversations, fetchUnreadCount,
    connectWebSocket, sendWsMessage, disconnectWebSocket
  }
})
