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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { getRecommendations, getPopularTextbooks } from '../api/modules'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const searchKeyword = ref('')
const recommendations = ref([])
const popular = ref([])

const getTypeTag = (type) => ({ sell: '', rent: 'warning', free: 'success' }[type] || '')
const getTypeLabel = (type) => ({ sell: '出售', rent: '租赁', free: '免费' }[type] || '')

onMounted(async () => {
  try {
    if (userStore.isLoggedIn) {
      const res = await getRecommendations({ limit: 8 })
      recommendations.value = res.data.recommendations || []
    }
  } catch {}
  try {
    const res = await getPopularTextbooks()
    popular.value = (res.data.results || res.data).slice(0, 8)
  } catch {}
})

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/textbooks', query: { q: searchKeyword.value.trim() } })
  }
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
</style>
