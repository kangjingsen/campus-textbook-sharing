<template>
  <div class="my-resources">
    <el-card>
      <template #header>
        <div class="header">
          <h2>📁 我的在线资料</h2>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="按标题/描述/分类模糊搜索"
              clearable
              style="width: 260px;"
              @keyup.enter="loadData"
              @clear="loadData"
            />
            <el-select v-model="saleType" placeholder="收费方式" clearable style="width: 120px;" @change="loadData">
              <el-option label="免费" value="free" />
              <el-option label="售卖" value="sell" />
            </el-select>
            <el-select v-model="resourceType" placeholder="类型" clearable style="width: 120px;" @change="loadData">
              <el-option label="PDF" value="pdf" />
              <el-option label="Word" value="doc" />
              <el-option label="PPT" value="ppt" />
              <el-option label="其他" value="other" />
            </el-select>
            <el-dropdown @command="handleExport">
              <el-button>批量导出</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="xlsx">导出 Excel</el-dropdown-item>
                  <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="primary" @click="$router.push('/resources')">上传资料</el-button>
          </div>
        </div>
      </template>

      <el-table :data="resources" v-loading="loading" stripe>
        <el-table-column label="资料信息" min-width="280">
          <template #default="{ row }">
            <div class="resource-info">
              <strong>{{ row.title }}</strong>
              <div class="meta">{{ row.category_name || '未分类' }} · {{ row.resource_type_display }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="sale_type_display" label="收费方式" width="100" />
        <el-table-column label="价格" width="100">
          <template #default="{ row }">
            <span v-if="row.sale_type === 'sell'" class="price">¥{{ row.price }}</span>
            <span v-else class="free">免费</span>
          </template>
        </el-table-column>
        <el-table-column prop="download_count" label="下载" width="80" />
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button text type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          :page-size="20"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMyResources, exportMyResources, deleteResource } from '../api/modules'

const resources = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const searchKeyword = ref('')
const saleType = ref('')
const resourceType = ref('')

onMounted(() => loadData())

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value }
    if (searchKeyword.value.trim()) params.q = searchKeyword.value.trim()
    if (saleType.value) params.sale_type = saleType.value
    if (resourceType.value) params.resource_type = resourceType.value
    const res = await getMyResources(params)
    resources.value = res.data.results || res.data || []
    total.value = res.data.count || resources.value.length
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

const handleExport = async (format) => {
  try {
    const res = await exportMyResources({
      format,
      q: searchKeyword.value.trim() || undefined,
      sale_type: saleType.value || undefined,
      resource_type: resourceType.value || undefined
    })
    downloadBlob(res.data, format === 'xlsx' ? 'my_resources.xlsx' : 'my_resources.csv')
  } catch {
    ElMessage.error('导出失败，请稍后重试')
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该资料？', '提示', { type: 'warning' })
    await deleteResource(id)
    ElMessage.success('已删除')
    await loadData()
  } catch {}
}
</script>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; }
.header-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.resource-info strong { display: block; }
.meta { color: #909399; font-size: 12px; margin-top: 4px; }
.price { color: #f56c6c; font-weight: bold; }
.free { color: #67c23a; }
.pagination { text-align: center; margin-top: 16px; }
</style>
