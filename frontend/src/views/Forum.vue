<template>
  <div class="forum-page">
    <el-card class="toolbar-card">
      <div class="toolbar-row">
        <div class="left">
          <el-radio-group v-model="topicType" @change="loadTopics">
            <el-radio-button label="全部" value="" />
            <el-radio-button label="讨论" value="discussion" />
            <el-radio-button label="问答" value="question" />
          </el-radio-group>
          <el-input v-model="keyword" placeholder="搜索帖子标题" style="width: 260px" @keyup.enter="loadTopics" clearable />
          <el-button type="primary" @click="loadTopics">筛选</el-button>
        </div>
        <el-button type="success" @click="openCreate" :disabled="!userStore.isLoggedIn">发布帖子</el-button>
      </div>
    </el-card>

    <el-row :gutter="16" style="margin-top: 12px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="list-header">论坛主题</div>
          </template>
          <el-table :data="topics" v-loading="loading" stripe>
            <el-table-column label="标题" min-width="280">
              <template #default="{ row }">
                <div class="title-cell" @click="openDetail(row.id)">
                  <el-tag size="small" :type="row.topic_type === 'question' ? 'warning' : ''">
                    {{ row.topic_type === 'question' ? '问答' : '讨论' }}
                  </el-tag>
                  <span class="title-text">{{ row.title }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="作者" width="140">
              <template #default="{ row }">
                <el-link type="primary" @click.stop="goUserProfile(row.creator)">{{ row.creator_name }}</el-link>
              </template>
            </el-table-column>
            <el-table-column prop="reply_count" label="回复" width="90" />
            <el-table-column prop="view_count" label="浏览" width="90" />
            <el-table-column prop="created_at" label="发布时间" width="170" />
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button
                  v-if="canDeleteTopic(row)"
                  type="danger"
                  text
                  size="small"
                  @click.stop="handleDeleteTopic(row.id)"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="list-header">公告资讯</div>
          </template>
          <div v-for="item in announcements" :key="item.id" class="announcement-item">
            <div class="announcement-title">{{ item.title }}</div>
            <div class="announcement-summary">{{ item.summary || item.content }}</div>
          </div>
          <el-empty v-if="!announcements.length" description="暂无公告" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="createVisible" title="发布帖子" width="640px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="类型">
          <el-radio-group v-model="createForm.topic_type">
            <el-radio-button value="discussion">讨论</el-radio-button>
            <el-radio-button value="question">问答</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="createForm.title" maxlength="220" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="createForm.content" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="creating">发布</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" width="760px" :title="detail?.title || '帖子详情'">
      <div v-if="detail" class="detail-body">
        <div class="detail-meta-row">
          <div class="detail-meta">
            <el-link type="primary" @click="goUserProfile(detail.creator)">{{ detail.creator_name }}</el-link>
            <span> · {{ detail.created_at }}</span>
          </div>
          <el-button
            v-if="canDeleteTopic(detail)"
            type="danger"
            plain
            size="small"
            @click="handleDeleteTopic(detail.id)"
          >删除帖子</el-button>
        </div>
        <div class="detail-content">{{ detail.content }}</div>

        <div class="reply-header">回复区</div>
        <div v-for="reply in detail.replies || []" :key="reply.id" class="reply-item">
          <div class="reply-line">
            <strong>{{ reply.username }}</strong>
            <el-tag v-if="reply.is_best_answer" type="success" size="small">最佳回答</el-tag>
            <span class="reply-time">{{ reply.created_at }}</span>
          </div>
          <div>{{ reply.content }}</div>
          <el-button
            v-if="canMarkBest(reply)"
            text
            type="success"
            size="small"
            @click="handleMarkBest(reply.id)"
          >设为最佳回答</el-button>
        </div>

        <el-input
          v-if="userStore.isLoggedIn"
          v-model="replyContent"
          type="textarea"
          :rows="3"
          placeholder="写下你的回复..."
        />
        <div style="margin-top: 8px; text-align: right;" v-if="userStore.isLoggedIn">
          <el-button type="primary" @click="submitReply" :loading="replying">提交回复</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../stores/user'
import {
  createForumReply,
  createForumTopic,
  deleteForumTopic,
  getAnnouncements,
  getForumTopicDetail,
  getForumTopics,
  markBestAnswer
} from '../api/modules'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const replying = ref(false)
const createVisible = ref(false)
const detailVisible = ref(false)

const topicType = ref('')
const keyword = ref('')
const topics = ref([])
const announcements = ref([])
const detail = ref(null)
const replyContent = ref('')

const createForm = reactive({
  title: '',
  content: '',
  topic_type: 'discussion'
})

const loadTopics = async () => {
  loading.value = true
  try {
    const res = await getForumTopics({ topic_type: topicType.value, q: keyword.value })
    topics.value = res.data.results || res.data || []
  } finally {
    loading.value = false
  }
}

const loadAnnouncements = async () => {
  try {
    const res = await getAnnouncements({ page_size: 6 })
    announcements.value = res.data.results || res.data || []
  } catch {
    console.warn('公告加载失败')
  }
}

const openCreate = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后发帖')
    return
  }
  createForm.title = ''
  createForm.content = ''
  createForm.topic_type = 'discussion'
  createVisible.value = true
}

const submitCreate = async () => {
  if (!createForm.title.trim() || !createForm.content.trim()) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  creating.value = true
  try {
    await createForumTopic(createForm)
    createVisible.value = false
    ElMessage.success('发布成功')
    await loadTopics()
  } finally {
    creating.value = false
  }
}

const openDetail = async (id) => {
  const res = await getForumTopicDetail(id)
  detail.value = res.data
  detailVisible.value = true
}

const submitReply = async () => {
  if (!detail.value?.id || !replyContent.value.trim()) return
  replying.value = true
  try {
    await createForumReply(detail.value.id, { content: replyContent.value.trim() })
    replyContent.value = ''
    const res = await getForumTopicDetail(detail.value.id)
    detail.value = res.data
    await loadTopics()
  } finally {
    replying.value = false
  }
}

const canMarkBest = (reply) => {
  if (!detail.value || !userStore.isLoggedIn) return false
  return detail.value.topic_type === 'question' && (userStore.user?.id === detail.value.creator || userStore.isAdmin) && !reply.is_best_answer
}

const goUserProfile = (userId) => {
  if (!userId) return
  router.push(`/user/${userId}`)
}

const canDeleteTopic = (topic) => {
  if (!topic || !userStore.isLoggedIn) return false
  return userStore.isAdmin || userStore.user?.id === topic.creator
}

const handleDeleteTopic = async (topicId) => {
  if (!topicId) return
  try {
    await ElMessageBox.confirm('确认删除该帖子吗？删除后不可恢复。', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteForumTopic(topicId)
    ElMessage.success('帖子已删除')
    if (detail.value?.id === topicId) {
      detailVisible.value = false
      detail.value = null
    }
    await loadTopics()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('删除帖子失败', error)
    }
  }
}

const handleMarkBest = async (replyId) => {
  if (!detail.value?.id) return
  await markBestAnswer(detail.value.id, replyId)
  ElMessage.success('已设置最佳回答')
  const res = await getForumTopicDetail(detail.value.id)
  detail.value = res.data
}

onMounted(async () => {
  await Promise.all([loadTopics(), loadAnnouncements()])
  const topicId = Number(route.query.topic_id)
  if (topicId) {
    await openDetail(topicId)
  }
})
</script>

<style scoped>
.toolbar-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.left { display: flex; gap: 10px; align-items: center; }
.title-cell { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.title-text { color: #303133; }
.list-header { font-weight: 600; }
.announcement-item { padding: 8px 0; border-bottom: 1px solid #f0f2f5; }
.announcement-title { font-weight: 600; margin-bottom: 4px; }
.announcement-summary { color: #606266; font-size: 13px; }
.detail-meta-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.detail-meta { color: #909399; margin-bottom: 8px; }
.detail-content { white-space: pre-wrap; margin-bottom: 16px; }
.reply-header { font-weight: 600; margin: 10px 0; }
.reply-item { padding: 10px 0; border-bottom: 1px dashed #ebeef5; }
.reply-line { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.reply-time { color: #909399; font-size: 12px; }
</style>
