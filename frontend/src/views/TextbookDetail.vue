<template>
  <div class="detail-page" v-loading="loading">
    <el-row :gutter="24" v-if="textbook">
      <!-- 左侧封面 -->
      <el-col :span="8">
        <el-card>
          <div class="cover-wrapper">
            <img :src="textbook.cover_image || '/placeholder.png'" alt="" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧信息 -->
      <el-col :span="16">
        <el-card>
          <div class="info-header">
            <h1>{{ textbook.title }}</h1>
            <el-tag :type="getTypeTag(textbook.transaction_type)" size="large">
              {{ textbook.transaction_type_display }}
            </el-tag>
          </div>

          <el-descriptions :column="2" border class="info-desc">
            <el-descriptions-item label="作者">{{ textbook.author }}</el-descriptions-item>
            <el-descriptions-item label="ISBN">{{ textbook.isbn || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="出版社">{{ textbook.publisher || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="版次">{{ textbook.edition || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="新旧程度">
              <el-rate :model-value="textbook.condition" disabled />
              {{ textbook.condition_display }}
            </el-descriptions-item>
            <el-descriptions-item label="分类">{{ textbook.category_name || '未分类' }}</el-descriptions-item>
            <el-descriptions-item label="浏览量">{{ textbook.view_count }}</el-descriptions-item>
            <el-descriptions-item label="发布时间">{{ textbook.created_at }}</el-descriptions-item>
          </el-descriptions>

          <div class="price-section">
            <span class="price" v-if="textbook.transaction_type !== 'free'">¥{{ textbook.price }}</span>
            <span class="price free" v-else>免费赠送</span>
            <span v-if="textbook.original_price" class="original-price">原价 ¥{{ textbook.original_price }}</span>
            <span v-if="textbook.transaction_type === 'rent'" class="rent-info">
              租赁{{ textbook.rent_duration }}天
            </span>
          </div>

          <div class="description" v-if="textbook.description">
            <h3>教材描述</h3>
            <p>{{ textbook.description }}</p>
          </div>

          <!-- 点赞/点踩 -->
          <div class="vote-section">
            <el-button :type="myVote === 1 ? 'primary' : ''" @click="handleVote(1)" :icon="CaretTop" round>
              👍 {{ likes }}
            </el-button>
            <el-button :type="myVote === -1 ? 'danger' : ''" @click="handleVote(-1)" :icon="CaretBottom" round>
              👎 {{ dislikes }}
            </el-button>
          </div>

          <!-- 发布者信息 -->
          <div class="owner-info" @click="$router.push(`/user/${textbook.owner}`)" style="cursor: pointer;">
            <el-avatar :size="40" :src="textbook.owner_avatar" />
            <div>
              <p class="owner-name">{{ textbook.owner_name }} <el-text type="info" size="small">点击查看主页</el-text></p>
              <p class="owner-college">{{ textbook.owner_college }}</p>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="actions" v-if="userStore.isLoggedIn">
            <template v-if="textbook.owner !== userStore.user?.id">
              <el-button type="primary" size="large" @click="handleOrder" :disabled="textbook.status !== 'approved'">
                {{ textbook.transaction_type === 'rent' ? '租赁' : textbook.transaction_type === 'free' ? '申请领取' : '购买' }}
              </el-button>
              <el-button size="large" @click="handleChat">💬 联系卖家</el-button>
            </template>
            <template v-else>
              <el-button @click="$router.push(`/publish?edit=${textbook.id}`)">编辑</el-button>
              <el-button type="danger" @click="handleDelete">删除</el-button>
            </template>
            <!-- 管理员可删除任何人的教材 -->
            <el-button v-if="userStore.isAdmin && textbook.owner !== userStore.user?.id"
                       type="danger" @click="handleAdminDelete">🗑 管理员删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 评论区 -->
    <el-card style="margin-top: 20px;" v-if="textbook">
      <template #header><span>💬 评论区 ({{ comments.length }})</span></template>

      <!-- 发表评论 -->
      <div class="comment-input" v-if="userStore.isLoggedIn">
        <el-input v-model="newComment" type="textarea" :rows="3" placeholder="写下你的评论..."
                  maxlength="500" show-word-limit />
        <el-button type="primary" style="margin-top: 8px;" @click="submitComment" :disabled="!newComment.trim()">
          发表评论
        </el-button>
      </div>
      <el-alert v-else type="info" :closable="false" style="margin-bottom: 16px;">
        <router-link to="/login">登录</router-link> 后即可评论
      </el-alert>

      <!-- 评论列表 -->
      <div class="comment-list">
        <div v-for="comment in comments" :key="comment.id" class="comment-item">
          <el-avatar :size="36" :src="comment.avatar" style="cursor:pointer" @click="$router.push(`/user/${comment.user}`)" />
          <div class="comment-body">
            <div class="comment-meta">
              <span class="comment-user" style="cursor:pointer" @click="$router.push(`/user/${comment.user}`)">{{ comment.username }}</span>
              <span class="comment-time">{{ comment.created_at }}</span>
              <el-button v-if="userStore.user?.id === comment.user || userStore.isAdmin"
                         type="danger" link size="small" @click="handleDeleteComment(comment.id)">删除</el-button>
            </div>
            <p class="comment-content">{{ comment.content }}</p>
            <!-- 回复 -->
            <div v-if="comment.replies?.length" class="replies">
              <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                <span class="comment-user" style="cursor:pointer" @click="$router.push(`/user/${reply.user}`)">{{ reply.username }}</span>：
                <span>{{ reply.content }}</span>
                <span class="comment-time">{{ reply.created_at }}</span>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-if="!comments.length" description="暂无评论" />
      </div>
    </el-card>

    <!-- 下单对话框 -->
    <el-dialog v-model="orderDialogVisible" title="确认下单" width="480px">
      <el-form :model="orderForm" label-width="100px">
        <el-form-item label="教材">{{ textbook?.title }}</el-form-item>
        <el-form-item label="价格">
          <span class="price">¥{{ textbook?.price }}</span>
        </el-form-item>
        <el-form-item label="交易类型">{{ textbook?.transaction_type_display }}</el-form-item>
        <el-form-item v-if="textbook?.transaction_type === 'rent'" label="租赁日期">
          <el-date-picker v-model="orderForm.dateRange" type="daterange"
                          start-placeholder="开始日期" end-placeholder="结束日期"
                          value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="orderForm.note" type="textarea" placeholder="给卖家留言..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="orderDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitOrder" :loading="orderLoading">确认下单</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CaretTop, CaretBottom } from '@element-plus/icons-vue'
import {
  getTextbookDetail, createOrder, deleteTextbook, createConversation,
  getTextbookVotes, voteTextbook,
  getTextbookComments, createComment, deleteComment,
  adminDeleteTextbook
} from '../api/modules'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const textbook = ref(null)
const loading = ref(true)
const orderDialogVisible = ref(false)
const orderLoading = ref(false)
const orderForm = reactive({ note: '', dateRange: null })

// 投票
const likes = ref(0)
const dislikes = ref(0)
const myVote = ref(0)

// 评论
const comments = ref([])
const newComment = ref('')

const getTypeTag = (type) => ({ sell: '', rent: 'warning', free: 'success' }[type] || '')

onMounted(async () => {
  const id = route.params.id
  try {
    const [detailRes, voteRes, commentRes] = await Promise.all([
      getTextbookDetail(id),
      getTextbookVotes(id).catch(() => ({ data: { likes: 0, dislikes: 0, my_vote: 0 } })),
      getTextbookComments(id).catch(() => ({ data: { results: [] } }))
    ])
    textbook.value = detailRes.data
    likes.value = voteRes.data.likes
    dislikes.value = voteRes.data.dislikes
    myVote.value = voteRes.data.my_vote
    comments.value = commentRes.data.results || commentRes.data || []
  } catch {
    ElMessage.error('教材不存在')
    router.push('/textbooks')
  } finally {
    loading.value = false
  }
})

const handleVote = async (val) => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    const res = await voteTextbook(route.params.id, val)
    likes.value = res.data.likes
    dislikes.value = res.data.dislikes
    myVote.value = res.data.my_vote
  } catch {}
}

const submitComment = async () => {
  try {
    await createComment(route.params.id, { content: newComment.value })
    newComment.value = ''
    // 重新加载评论
    const res = await getTextbookComments(route.params.id)
    comments.value = res.data.results || res.data || []
    ElMessage.success('评论成功')
  } catch {}
}

const handleDeleteComment = async (commentId) => {
  try {
    await ElMessageBox.confirm('确定删除该评论？', '提示', { type: 'warning' })
    await deleteComment(commentId)
    const res = await getTextbookComments(route.params.id)
    comments.value = res.data.results || res.data || []
    ElMessage.success('已删除')
  } catch {}
}

const handleOrder = () => {
  orderDialogVisible.value = true
}

const submitOrder = async () => {
  orderLoading.value = true
  try {
    const data = {
      textbook_id: textbook.value.id,
      note: orderForm.note
    }
    if (orderForm.dateRange) {
      data.rent_start_date = orderForm.dateRange[0]
      data.rent_end_date = orderForm.dateRange[1]
    }
    await createOrder(data)
    ElMessage.success('下单成功！等待卖家确认')
    orderDialogVisible.value = false
    router.push('/orders')
  } catch {} finally {
    orderLoading.value = false
  }
}

const handleChat = async () => {
  try {
    const res = await createConversation({ user_id: textbook.value.owner })
    router.push({ path: '/chat', query: { id: res.data.id } })
  } catch {}
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定删除该教材？', '提示', { type: 'warning' })
    await deleteTextbook(textbook.value.id)
    ElMessage.success('删除成功')
    router.push('/my-textbooks')
  } catch {}
}

const handleAdminDelete = async () => {
  try {
    await ElMessageBox.confirm('管理员操作：确定删除该教材？此操作不可撤销', '管理员删除', { type: 'warning' })
    await adminDeleteTextbook(textbook.value.id)
    ElMessage.success('已删除')
    router.push('/textbooks')
  } catch {}
}
</script>

<style scoped>
.cover-wrapper {
  display: flex; align-items: center; justify-content: center;
  min-height: 400px; background: #f5f7fa; border-radius: 8px;
}
.cover-wrapper img { max-width: 100%; max-height: 400px; object-fit: contain; }
.info-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.info-header h1 { font-size: 24px; }
.info-desc { margin-bottom: 20px; }
.price-section { margin: 20px 0; }
.price { font-size: 28px; color: #f56c6c; font-weight: bold; }
.price.free { color: #67c23a; }
.original-price { color: #909399; text-decoration: line-through; margin-left: 12px; font-size: 14px; }
.rent-info { color: #e6a23c; margin-left: 12px; }
.description { margin: 20px 0; }
.description h3 { font-size: 16px; margin-bottom: 8px; }
.description p { color: #606266; line-height: 1.8; }
.vote-section { display: flex; gap: 12px; margin: 16px 0; }
.owner-info { display: flex; align-items: center; gap: 12px; padding: 16px; background: #f5f7fa; border-radius: 8px; margin: 20px 0; }
.owner-name { font-weight: bold; }
.owner-college { color: #909399; font-size: 13px; }
.actions { display: flex; gap: 12px; margin-top: 20px; }

/* 评论区 */
.comment-input { margin-bottom: 20px; }
.comment-list { margin-top: 12px; }
.comment-item { display: flex; gap: 12px; padding: 16px 0; border-bottom: 1px solid #ebeef5; }
.comment-body { flex: 1; }
.comment-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.comment-user { font-weight: bold; font-size: 14px; color: #303133; }
.comment-time { color: #909399; font-size: 12px; }
.comment-content { color: #606266; line-height: 1.6; margin: 0; }
.replies { margin-top: 8px; padding: 8px 12px; background: #f5f7fa; border-radius: 6px; }
.reply-item { margin: 4px 0; font-size: 13px; color: #606266; }
</style>
