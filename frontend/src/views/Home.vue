<template>
  <div class="home-page">
    <!-- Hero Banner -->
    <div class="hero">
      <h1>📚 校园教材共享平台</h1>
      <p>买卖、租赁、赠送 — 让知识流动起来</p>
      <el-input v-model="searchKeyword" placeholder="搜索书名、作者、ISBN..." size="large"
                style="max-width: 500px;" @keyup.enter="handleSearch" clearable>
        <template #append>
          <el-button :icon="Search" @click="handleSearch" />
        </template>
      </el-input>
    </div>

    <!-- 推荐教材 -->
    <div class="section" v-if="userStore.isLoggedIn">
      <div class="section-header">
        <h2>💖 我的心愿单（高优先级）</h2>
        <router-link to="/wishlist">管理心愿单 →</router-link>
      </div>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" v-for="wish in wishlistTop" :key="wish.id">
          <el-card shadow="hover" class="wishlist-card">
            <div class="wish-top">
              <h4>{{ wish.title }}</h4>
              <el-tag :type="statusType(wish.status)" size="small">{{ statusText(wish.status) }}</el-tag>
            </div>
            <p class="wish-meta">作者：{{ wish.author || '不限' }}</p>
            <p class="wish-meta">分类：{{ wish.category_name || '未指定' }}</p>
            <div class="wish-actions">
              <el-rate v-model="wish.priority" disabled :max="5" />
              <el-button size="small" type="primary" @click="handleWishSearch(wish.title)">去找书</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="!wishlistTop.length" description="还没有心愿，去添加一条吧" />
    </div>

    <div class="section">
      <div class="section-header">
        <h2>🎯 为你推荐</h2>
        <router-link to="/textbooks">查看全部 →</router-link>
      </div>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in recommendations" :key="item.id">
          <el-card shadow="hover" class="textbook-card" @click="$router.push(`/textbooks/${item.id || item.textbook?.id}`)">
            <div class="card-cover">
              <img :src="item.cover_image || item.textbook?.cover_image || '/placeholder.png'" alt="" />
              <el-tag class="card-type" :type="getTypeTag(item.transaction_type || item.textbook?.transaction_type)" size="small">
                {{ getTypeLabel(item.transaction_type || item.textbook?.transaction_type) }}
              </el-tag>
            </div>
            <div class="card-info">
              <h4>{{ item.title || item.textbook?.title }}</h4>
              <p class="author">{{ item.author || item.textbook?.author }}</p>
              <div class="card-bottom">
                <span class="price" v-if="(item.transaction_type || item.textbook?.transaction_type) !== 'free'">
                  ¥{{ item.price || item.textbook?.price }}
                </span>
                <span class="price free" v-else>免费</span>
                <span class="views">👁 {{ item.view_count || item.textbook?.view_count || 0 }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="!recommendations.length" description="暂无推荐" />
    </div>

    <!-- 热门教材 -->
    <div class="section">
      <div class="section-header">
        <h2>🔥 热门教材</h2>
      </div>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in popular" :key="item.id">
          <el-card shadow="hover" class="textbook-card" @click="$router.push(`/textbooks/${item.id}`)">
            <div class="card-cover">
              <img :src="item.cover_image || '/placeholder.png'" alt="" />
              <el-tag class="card-type" :type="getTypeTag(item.transaction_type)" size="small">
                {{ getTypeLabel(item.transaction_type) }}
              </el-tag>
            </div>
            <div class="card-info">
              <h4>{{ item.title }}</h4>
              <p class="author">{{ item.author }}</p>
              <div class="card-bottom">
                <span class="price" v-if="item.transaction_type !== 'free'">¥{{ item.price }}</span>
                <span class="price free" v-else>免费</span>
                <span class="views">👁 {{ item.view_count }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="section">
      <div class="section-header">
        <h2>📢 公告资讯</h2>
        <router-link to="/forum">进入论坛 →</router-link>
      </div>
      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <el-card
            class="info-card"
            v-for="item in announcements"
            :key="item.id"
            style="margin-bottom: 12px; cursor: pointer;"
            @click="openAnnouncementDetail(item)"
          >
            <h4>{{ item.title }}</h4>
            <p class="info-text">{{ item.summary || item.content }}</p>
          </el-card>
          <el-empty v-if="!announcements.length" description="暂无公告" />
        </el-col>
        <el-col :xs="24" :md="12">
          <el-card class="info-card" v-for="topic in forumTopics" :key="topic.id" style="margin-bottom: 12px; cursor: pointer;" @click="$router.push('/forum')">
            <h4>{{ topic.title }}</h4>
            <p class="info-text">{{ topic.creator_name }} · 回复 {{ topic.reply_count || 0 }} · 浏览 {{ topic.view_count || 0 }}</p>
          </el-card>
          <el-empty v-if="!forumTopics.length" description="暂无帖子" />
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="announcementDetailVisible" width="680px" :title="currentAnnouncement?.title || '公告详情'">
      <div v-if="currentAnnouncement" class="announcement-detail-content">
        <div class="announcement-detail-meta">发布时间：{{ currentAnnouncement.published_at || '-' }}</div>
        <div class="announcement-detail-text">{{ currentAnnouncement.content }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { getAnnouncements, getForumTopics, getRecommendations, getPopularTextbooks, getWishlist } from '../api/modules'
import { useUserStore } from '../stores/user'
import { useAppStore } from '../stores/app'

const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()
const searchKeyword = ref('')
const recommendations = ref([])
const popular = ref([])
const wishlistTop = ref([])
const announcements = ref([])
const forumTopics = ref([])
const announcementDetailVisible = ref(false)
const currentAnnouncement = ref(null)

const getTypeTag = (type) => ({ sell: '', rent: 'warning', free: 'success' }[type] || '')
const getTypeLabel = (type) => ({ sell: '出售', rent: '租赁', free: '免费' }[type] || '')
const statusText = (s) => ({ open: '待满足', matched: '已匹配', closed: '已关闭' }[s] || s)
const statusType = (s) => ({ open: 'warning', matched: 'success', closed: 'info' }[s] || '')

const loadPersonalizedSection = async (options = {}) => {
  const forceRefresh = Boolean(options.forceRefresh)
  try {
    if (userStore.isLoggedIn) {
      const res = await getRecommendations({ limit: 8, ...(forceRefresh ? { refresh: 1 } : {}) })
      recommendations.value = res.data.recommendations || []
      const wishRes = await getWishlist({ status: 'open' })
      const wishList = wishRes.data.results || wishRes.data || []
      wishlistTop.value = wishList.slice(0, 3)
    }
  } catch {}
}

onMounted(async () => {
  await loadPersonalizedSection()
  try {
    const res = await getPopularTextbooks()
    popular.value = (res.data.results || res.data).slice(0, 8)
  } catch {}
  try {
    const [aRes, fRes] = await Promise.allSettled([
      getAnnouncements({ page_size: 4 }),
      getForumTopics({ page_size: 4 }, { skipAuth: true })
    ])
    announcements.value = aRes.status === 'fulfilled' ? (aRes.value.data.results || aRes.value.data || []) : []
    forumTopics.value = fRes.status === 'fulfilled' ? (fRes.value.data.results || fRes.value.data || []) : []
  } catch {}

  window.addEventListener('wishlist-updated', loadPersonalizedSection)
})

watchEffect(() => {
  if (appStore.wishlistUpdateTime > 0) {
    loadPersonalizedSection({ forceRefresh: true })
  }
})

onUnmounted(() => {
  window.removeEventListener('wishlist-updated', loadPersonalizedSection)
})

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/textbooks', query: { q: searchKeyword.value.trim() } })
  }
}

const handleWishSearch = (title) => {
  if (!title) return
  router.push({ path: '/textbooks', query: { q: title } })
}

const openAnnouncementDetail = (item) => {
  if (!item) return
  currentAnnouncement.value = item
  announcementDetailVisible.value = true
}
</script>

<style scoped>
.hero {
  text-align: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: #fff;
  margin-bottom: 32px;
}
.hero h1 { font-size: 36px; margin-bottom: 12px; }
.hero p { font-size: 18px; margin-bottom: 24px; opacity: 0.9; }
.section { margin-bottom: 32px; }
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-header h2 { font-size: 20px; }
.section-header a { color: #409eff; text-decoration: none; }
.textbook-card { cursor: pointer; margin-bottom: 16px; border-radius: 8px; }
.textbook-card:hover { transform: translateY(-2px); transition: 0.3s; }
.card-cover {
  position: relative;
  height: 180px;
  overflow: hidden;
  border-radius: 4px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-cover img { max-height: 100%; max-width: 100%; object-fit: cover; }
.card-type { position: absolute; top: 8px; right: 8px; }
.card-info { padding-top: 12px; }
.card-info h4 {
  font-size: 15px;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.author { color: #909399; font-size: 13px; margin-bottom: 8px; }
.card-bottom { display: flex; justify-content: space-between; align-items: center; }
.price { color: #f56c6c; font-size: 16px; font-weight: bold; }
.price.free { color: #67c23a; }
.views { color: #909399; font-size: 12px; }
.wishlist-card { margin-bottom: 16px; }
.wish-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.wish-top h4 { margin:0; font-size: 15px; }
.wish-meta { color:#606266; margin: 4px 0; font-size: 13px; }
.wish-actions { display:flex; justify-content:space-between; align-items:center; margin-top:8px; }
.info-card h4 { margin: 0 0 6px; font-size: 15px; }
.info-text { margin: 0; color: #606266; font-size: 13px; }
.announcement-detail-meta { color: #909399; margin-bottom: 12px; }
.announcement-detail-text { white-space: pre-wrap; line-height: 1.8; color: #303133; }
</style>
