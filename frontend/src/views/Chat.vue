<template>
  <div class="chat-page">
    <el-row :gutter="0" class="chat-container">
      <!-- 会话列表 -->
      <el-col :span="8" class="conversation-list">
        <div class="conv-header">
          <h3>💬 消息</h3>
        </div>
        <div class="conv-items" v-loading="convLoading">
          <div v-for="conv in conversations" :key="conv.id"
               :class="['conv-item', { active: currentConvId === conv.id }]"
               @click="selectConversation(conv)">
            <el-avatar :size="42" :src="conv.other_user?.avatar" />
            <div class="conv-info">
              <div class="conv-top">
                <span class="conv-name">{{ conv.other_user?.username }}</span>
                <span class="conv-time">{{ formatTime(conv.last_message?.created_at) }}</span>
              </div>
              <div class="conv-preview">
                {{ conv.last_message?.content || '暂无消息' }}
              </div>
            </div>
            <el-badge v-if="conv.unread_count" :value="conv.unread_count" class="unread-badge" />
          </div>
          <el-empty v-if="!conversations.length && !convLoading" description="暂无会话" :image-size="60" />
        </div>
      </el-col>

      <!-- 聊天区域 -->
      <el-col :span="16" class="chat-area">
        <template v-if="currentConvId">
          <div class="chat-header">
            <span>{{ currentConv?.other_user?.username }}</span>
            <span class="college">{{ currentConv?.other_user?.college }}</span>
          </div>

          <div class="messages-container" ref="messagesRef">
            <div v-for="msg in messages" :key="msg.id"
                 :class="['message', { mine: msg.sender === userStore.user?.id }]">
              <el-avatar :size="32" :src="msg.sender_avatar" />
              <div class="msg-content">
                <div class="msg-bubble">{{ msg.content }}</div>
                <div class="msg-time">{{ msg.created_at }}</div>
              </div>
            </div>
          </div>

          <div class="input-area">
            <el-input v-model="inputMessage" placeholder="输入消息..." @keyup.enter="sendMsg"
                      :rows="2" type="textarea" resize="none" />
            <el-button type="primary" @click="sendMsg" :disabled="!inputMessage.trim()">发送</el-button>
          </div>
        </template>
        <template v-else>
          <div class="no-chat">
            <el-empty description="选择一个会话开始聊天" :image-size="80" />
          </div>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getConversations, getMessages, sendMessage } from '../api/modules'
import { useUserStore } from '../stores/user'
import { useChatStore } from '../stores/chat'
import dayjs from 'dayjs'

const route = useRoute()
const userStore = useUserStore()
const chatStore = useChatStore()

const conversations = ref([])
const messages = ref([])
const currentConvId = ref(null)
const currentConv = ref(null)
const inputMessage = ref('')
const convLoading = ref(false)
const messagesRef = ref(null)

const formatTime = (time) => {
  if (!time) return ''
  const d = dayjs(time)
  const today = dayjs()
  if (d.isSame(today, 'day')) return d.format('HH:mm')
  return d.format('MM-DD HH:mm')
}

onMounted(async () => {
  await loadConversations()
  // 从URL参数中恢复会话
  if (route.query.id) {
    const conv = conversations.value.find(c => c.id == route.query.id)
    if (conv) selectConversation(conv)
  }
})

onUnmounted(() => {
  chatStore.disconnectWebSocket()
})

const loadConversations = async () => {
  convLoading.value = true
  try {
    const res = await getConversations()
    conversations.value = res.data.results || res.data
  } catch {} finally {
    convLoading.value = false
  }
}

const selectConversation = async (conv) => {
  currentConvId.value = conv.id
  currentConv.value = conv

  // 加载历史消息
  try {
    const res = await getMessages(conv.id)
    messages.value = res.data.results || res.data
    scrollToBottom()
  } catch {}

  // 连接 WebSocket
  const token = localStorage.getItem('access_token')
  chatStore.connectWebSocket(conv.id, token, (data) => {
    messages.value.push(data)
    scrollToBottom()
  })

  // 清除未读
  conv.unread_count = 0
}

const sendMsg = async () => {
  const content = inputMessage.value.trim()
  if (!content) return

  // 优先通过 WebSocket 发送
  chatStore.sendWsMessage(content)

  // 同时 HTTP 发送作为保底
  try {
    await sendMessage(currentConvId.value, { content })
  } catch {}

  inputMessage.value = ''
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-page { height: calc(100vh - 140px); }
.chat-container { height: 100%; border: 1px solid #ebeef5; border-radius: 8px; overflow: hidden; background: #fff; }
.conversation-list { border-right: 1px solid #ebeef5; height: 100%; display: flex; flex-direction: column; }
.conv-header { padding: 16px; border-bottom: 1px solid #ebeef5; }
.conv-header h3 { margin: 0; }
.conv-items { flex: 1; overflow-y: auto; }
.conv-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; cursor: pointer; position: relative;
  border-bottom: 1px solid #f5f7fa;
}
.conv-item:hover { background: #f5f7fa; }
.conv-item.active { background: #ecf5ff; }
.conv-info { flex: 1; min-width: 0; }
.conv-top { display: flex; justify-content: space-between; margin-bottom: 4px; }
.conv-name { font-weight: 500; font-size: 14px; }
.conv-time { color: #909399; font-size: 12px; }
.conv-preview { color: #909399; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.unread-badge { position: absolute; top: 8px; right: 8px; }

.chat-area { height: 100%; display: flex; flex-direction: column; }
.chat-header { padding: 16px; border-bottom: 1px solid #ebeef5; font-weight: 500; }
.college { color: #909399; font-size: 12px; margin-left: 8px; }
.messages-container { flex: 1; overflow-y: auto; padding: 16px; }
.message { display: flex; gap: 8px; margin-bottom: 16px; }
.message.mine { flex-direction: row-reverse; }
.msg-content { max-width: 60%; }
.msg-bubble {
  padding: 10px 14px; border-radius: 12px; background: #f5f7fa;
  word-break: break-word; line-height: 1.5;
}
.message.mine .msg-bubble { background: #409eff; color: #fff; }
.msg-time { font-size: 11px; color: #909399; margin-top: 4px; }
.message.mine .msg-time { text-align: right; }

.input-area { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid #ebeef5; }
.input-area .el-button { align-self: flex-end; }

.no-chat { display: flex; align-items: center; justify-content: center; height: 100%; }
</style>
