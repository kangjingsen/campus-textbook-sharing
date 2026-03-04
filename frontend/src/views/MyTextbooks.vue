<template>
  <div class="my-textbooks">
    <el-card>
      <template #header>
        <div class="header">
          <h2>📦 我的教材</h2>
          <el-button type="primary" @click="$router.push('/publish')">发布教材</el-button>
        </div>
      </template>

      <el-table :data="textbooks" v-loading="loading" stripe>
        <el-table-column label="教材信息" min-width="250">
          <template #default="{ row }">
            <div class="book-info" @click="$router.push(`/textbooks/${row.id}`)" style="cursor: pointer;">
              <strong>{{ row.title }}</strong>
              <div class="meta">{{ row.author }} · {{ row.category_name || '未分类' }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="transaction_type_display" label="交易类型" width="100" />
        <el-table-column label="价格" width="100">
          <template #default="{ row }">
            <span v-if="row.transaction_type !== 'free'" class="price">¥{{ row.price }}</span>
            <span v-else class="free">免费</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览" width="80" />
        <el-table-column prop="created_at" label="发布时间" width="160" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="$router.push(`/publish?edit=${row.id}`)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="total > 0">
        <el-pagination v-model:current-page="page" :page-size="20" :total="total"
                       layout="prev, pager, next" @current-change="loadData" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMyTextbooks, deleteTextbook } from '../api/modules'

const textbooks = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)

const getStatusType = (s) => ({
  pending_review: 'warning', approved: 'success', rejected: 'danger',
  sold: 'info', rented: 'info', offline: 'info'
}[s] || '')

onMounted(() => loadData())

const loadData = async () => {
  loading.value = true
  try {
    const res = await getMyTextbooks({ page: page.value })
    textbooks.value = res.data.results || res.data
    total.value = res.data.count || textbooks.value.length
  } catch {} finally {
    loading.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
    await deleteTextbook(id)
    ElMessage.success('已删除')
    loadData()
  } catch {}
}
</script>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; }
.book-info strong { display: block; }
.meta { color: #909399; font-size: 12px; margin-top: 4px; }
.price { color: #f56c6c; font-weight: bold; }
.free { color: #67c23a; }
.pagination { text-align: center; margin-top: 16px; }
</style>
