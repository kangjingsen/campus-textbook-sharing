<template>
  <div class="user-profile-page" v-loading="loading">
    <el-row :gutter="20" v-if="user">
      <!-- 左侧用户信息 -->
      <el-col :span="8">
        <el-card class="info-card">
          <div class="avatar-section">
            <el-avatar :size="100" :src="user.avatar" />
          </div>
          <div class="user-summary">
            <h3>{{ user.username }}</h3>
            <p><el-icon><School /></el-icon> {{ user.college || '未填写学院' }}</p>
            <p><el-icon><Reading /></el-icon> {{ user.major || '未填写专业' }}</p>
            <el-tag :type="roleTagType" style="margin-top: 8px;">{{ roleLabel }}</el-tag>
          </div>
          <el-divider />
          <div class="user-detail">
            <p v-if="user.bio">📝 {{ user.bio }}</p>
            <p v-else style="color: #909399;">暂无个人简介</p>
            <p style="color: #909399; font-size: 12px; margin-top: 12px;">
              注册于 {{ user.date_joined?.slice(0, 10) }}
            </p>
          </div>
          <div class="user-actions" v-if="userStore.isLoggedIn && user.id !== userStore.user?.id">
            <el-button type="primary" @click="handleChat">💬 发消息</el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧 TA 的教材 -->
      <el-col :span="16">
        <el-card>
          <template #header><span>📚 TA 发布的教材 ({{ textbooks.length }})</span></template>
          <el-row :gutter="16">
            <el-col :xs="24" :sm="12" :md="8" v-for="item in textbooks" :key="item.id">
              <el-card shadow="hover" class="textbook-card" @click="$router.push(`/textbooks/${item.id}`)">
                <div class="card-cover">
                  <img :src="item.cover_image || '/placeholder.png'" alt="" />
                  <el-tag class="card-type" :type="getTypeTag(item.transaction_type)" size="small">
                    {{ item.transaction_type_display }}
                  </el-tag>
                </div>
                <div class="card-info">
                  <h4>{{ item.title }}</h4>
                  <p class="meta">{{ item.author }}</p>
                  <div class="card-bottom">
                    <span class="price" v-if="item.transaction_type !== 'free'">¥{{ item.price }}</span>
                    <span class="price free" v-else>免费</span>
                    <span class="condition">{{ item.condition_display }}</span>
                  </div>
                  <div class="card-footer">
                    <span>👍{{ item.likes_count || 0 }} 👎{{ item.dislikes_count || 0 }}</span>
                    <span>👁 {{ item.view_count }}</span>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
          <el-empty v-if="!textbooks.length && !loading" description="TA 还没有发布教材" />
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="!user && !loading" description="用户不存在" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { School, Reading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getUserDetail, getTextbooks, createConversation } from '../api/modules'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const user = ref(null)
const textbooks = ref([])
const loading = ref(true)

const roleLabel = computed(() => {
  const map = { student: '学生', admin: '管理员', superadmin: '超级管理员' }
  return map[user.value?.role] || '学生'
})
const roleTagType = computed(() => {
  const map = { student: '', admin: 'warning', superadmin: 'danger' }
  return map[user.value?.role] || ''
})

const getTypeTag = (type) => ({ sell: '', rent: 'warning', free: 'success' }[type] || '')

onMounted(async () => {
  const userId = route.params.id
  // 如果是查看自己的主页，跳转到 /profile
  if (userStore.isLoggedIn && Number(userId) === userStore.user?.id) {
    router.replace('/profile')
    return
  }
  try {
    const [userRes, textbookRes] = await Promise.all([
      getUserDetail(userId),
      getTextbooks({ owner: userId }).catch(() => ({ data: { results: [] } }))
    ])
    user.value = userRes.data
    textbooks.value = textbookRes.data.results || textbookRes.data || []
  } catch {
    ElMessage.error('用户不存在')
  } finally {
    loading.value = false
  }
})

const handleChat = async () => {
  try {
    const res = await createConversation({ user_id: user.value.id })
    router.push({ path: '/chat', query: { id: res.data.id } })
  } catch {}
}
</script>

<style scoped>
.user-profile-page { padding: 10px; }
.avatar-section { text-align: center; }
.user-summary { text-align: center; margin-top: 16px; }
.user-summary h3 { margin-bottom: 8px; }
.user-summary p { color: #606266; font-size: 14px; margin-bottom: 4px; display: flex; align-items: center; justify-content: center; gap: 4px; }
.user-detail { padding: 0 12px; }
.user-actions { text-align: center; margin-top: 16px; }
.textbook-card { cursor: pointer; margin-bottom: 16px; border-radius: 8px; }
.textbook-card:hover { transform: translateY(-2px); transition: 0.3s; }
.card-cover { position: relative; height: 140px; overflow: hidden; border-radius: 4px; background: #f5f7fa; display: flex; align-items: center; justify-content: center; }
.card-cover img { max-height: 100%; max-width: 100%; object-fit: cover; }
.card-type { position: absolute; top: 8px; right: 8px; }
.card-info { padding-top: 10px; }
.card-info h4 { font-size: 14px; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta { color: #909399; font-size: 12px; margin-bottom: 6px; }
.card-bottom { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.price { color: #f56c6c; font-size: 16px; font-weight: bold; }
.price.free { color: #67c23a; }
.condition { color: #e6a23c; font-size: 12px; }
.card-footer { display: flex; justify-content: space-between; color: #909399; font-size: 12px; }
</style>
