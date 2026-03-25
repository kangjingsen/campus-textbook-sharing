<template>
  <div class="textbook-list-page">
    <el-row :gutter="24">
      <!-- 左侧分类筛选 -->
      <el-col :span="5">
        <el-card>
          <template #header><span>📁 分类筛选</span></template>
          <el-tree :data="categoryTree" :props="{ label: 'name', children: 'children' }"
                   node-key="id" highlight-current @node-click="handleCategoryClick"
                   default-expand-all />
          <el-button v-if="filters.category" text type="primary" @click="filters.category = ''; loadTextbooks()"
                     style="margin-top: 8px;">清除分类筛选</el-button>
        </el-card>
      </el-col>

      <!-- 右侧列表 -->
      <el-col :span="19">
        <!-- 筛选栏 -->
        <el-card class="filter-card">
          <el-row :gutter="16" align="middle">
            <el-col :span="6">
              <el-select v-model="filters.transaction_type" placeholder="交易类型" clearable @change="loadTextbooks">
                <el-option label="出售" value="sell" />
                <el-option label="租赁" value="rent" />
                <el-option label="免费赠送" value="free" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="filters.condition" placeholder="新旧程度" clearable @change="loadTextbooks">
                <el-option label="全新" :value="5" />
                <el-option label="九成新" :value="4" />
                <el-option label="七成新" :value="3" />
                <el-option label="五成新" :value="2" />
                <el-option label="较旧" :value="1" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="filters.ordering" placeholder="排序方式" @change="loadTextbooks">
                <el-option label="最新发布" value="-created_at" />
                <el-option label="价格最低" value="price" />
                <el-option label="价格最高" value="-price" />
                <el-option label="最多浏览" value="-view_count" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-input v-model="searchKeyword" placeholder="搜索..." clearable
                        @keyup.enter="handleSearch" @clear="handleClearSearch">
                <template #append>
                  <el-button :icon="Search" @click="handleSearch" />
                </template>
              </el-input>
            </el-col>
          </el-row>
        </el-card>

        <!-- 搜索标签 -->
        <div v-if="currentSearch" class="search-tag">
          <el-tag closable @close="handleClearSearch">搜索: {{ currentSearch }}</el-tag>
          <span class="result-count">共 {{ total }} 条结果</span>
        </div>

        <!-- 教材列表 -->
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="8" v-for="item in textbooks" :key="item.id">
            <el-card shadow="hover" class="textbook-card" @click="$router.push(`/textbooks/${item.id}`)">
              <div class="card-cover">
                <img :src="item.cover_image || '/placeholder.png'" alt="" />
                <el-tag class="card-type" :type="getTypeTag(item.transaction_type)" size="small">
                  {{ item.transaction_type_display }}
                </el-tag>
                <el-tag
                  v-if="item.status !== 'approved'"
                  class="card-status"
                  type="danger"
                  size="small"
                >
                  已售
                </el-tag>
              </div>
              <div class="card-info">
                <h4>{{ item.title }}</h4>
                <p class="meta">{{ item.author }} · {{ item.category_name }}</p>
                <div class="card-bottom">
                  <span class="price" v-if="item.transaction_type !== 'free'">¥{{ item.price }}</span>
                  <span class="price free" v-else>免费</span>
                  <span class="condition">{{ item.condition_display }}</span>
                </div>
                <div class="card-footer">
                  <span class="owner-link" @click.stop="$router.push(`/user/${item.owner}`)">{{ item.owner_name }}</span>
                  <span>�{{ item.likes_count || 0 }} 👎{{ item.dislikes_count || 0 }}</span>
                  <span>�👁 {{ item.view_count }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-empty v-if="!textbooks.length && !loading" description="暂无教材" />

        <!-- 分页 -->
        <div class="pagination-wrapper" v-if="total > 0">
          <el-pagination v-model:current-page="page" :page-size="20" :total="total"
                         layout="prev, pager, next, total" @current-change="loadTextbooks" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { getTextbooks, searchTextbooks, getCategoryTree } from '../api/modules'

const route = useRoute()
const textbooks = ref([])
const categoryTree = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const searchKeyword = ref('')
const currentSearch = ref('')

const filters = reactive({
  transaction_type: '',
  condition: '',
  category: '',
  ordering: '-created_at'
})

const getTypeTag = (type) => ({ sell: '', rent: 'warning', free: 'success' }[type] || '')

onMounted(async () => {
  // 加载分类树
  try {
    const res = await getCategoryTree()
    categoryTree.value = res.data.results || res.data
  } catch {}

  // 检查URL中的搜索参数
  if (route.query.q) {
    searchKeyword.value = route.query.q
    handleSearch()
  } else {
    loadTextbooks()
  }
})

watch(() => route.query.q, (val) => {
  if (val) {
    searchKeyword.value = val
    handleSearch()
  }
})

const loadTextbooks = async () => {
  loading.value = true
  try {
    const params = { page: page.value, ordering: filters.ordering }
    if (filters.transaction_type) params.transaction_type = filters.transaction_type
    if (filters.condition) params.condition = filters.condition
    if (filters.category) params.category = filters.category

    const res = await getTextbooks(params)
    textbooks.value = res.data.results || res.data
    total.value = res.data.count || textbooks.value.length
    currentSearch.value = ''
  } catch {} finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    loadTextbooks()
    return
  }
  loading.value = true
  try {
    const res = await searchTextbooks({ q: searchKeyword.value.trim() })
    textbooks.value = res.data.results || []
    total.value = res.data.count || textbooks.value.length
    currentSearch.value = searchKeyword.value.trim()
  } catch {} finally {
    loading.value = false
  }
}

const handleClearSearch = () => {
  searchKeyword.value = ''
  currentSearch.value = ''
  loadTextbooks()
}

const handleCategoryClick = (data) => {
  filters.category = data.id
  loadTextbooks()
}
</script>

<style scoped>
.filter-card { margin-bottom: 16px; }
.search-tag { margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }
.result-count { color: #909399; font-size: 13px; }
.textbook-card { cursor: pointer; margin-bottom: 16px; border-radius: 8px; }
.textbook-card:hover { transform: translateY(-2px); transition: 0.3s; }
.card-cover {
  position: relative; height: 160px; overflow: hidden; border-radius: 4px;
  background: #f5f7fa; display: flex; align-items: center; justify-content: center;
}
.card-cover img { max-height: 100%; max-width: 100%; object-fit: cover; }
.card-type { position: absolute; top: 8px; right: 8px; }
.card-status { position: absolute; top: 8px; left: 8px; }
.card-info { padding-top: 10px; }
.card-info h4 { font-size: 14px; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta { color: #909399; font-size: 12px; margin-bottom: 6px; }
.card-bottom { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.price { color: #f56c6c; font-size: 16px; font-weight: bold; }
.price.free { color: #67c23a; }
.condition { color: #e6a23c; font-size: 12px; }
.card-footer { display: flex; justify-content: space-between; color: #909399; font-size: 12px; }
.owner-link { cursor: pointer; color: #409eff; }
.owner-link:hover { text-decoration: underline; }
.pagination-wrapper { text-align: center; margin-top: 24px; }
</style>
