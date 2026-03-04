<template>
  <div class="resources-page">
    <div class="page-header">
      <h2>📂 在线资料共享区</h2>
      <el-button v-if="userStore.isLoggedIn" type="primary" @click="uploadVisible = true">
        📤 上传资料
      </el-button>
    </div>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filters.resource_type" placeholder="资料类型" clearable @change="loadResources">
            <el-option label="PDF文档" value="pdf" />
            <el-option label="Word文档" value="doc" />
            <el-option label="PPT课件" value="ppt" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.category" placeholder="选择分类" clearable @change="loadResources">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.full_name || cat.name" :value="cat.id" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input v-model="filters.search" placeholder="搜索资料..." clearable @keyup.enter="loadResources">
            <template #append>
              <el-button @click="loadResources">搜索</el-button>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.ordering" @change="loadResources">
            <el-option label="最新上传" value="-created_at" />
            <el-option label="下载最多" value="-download_count" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- 资料列表 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="6" v-for="res in resources" :key="res.id">
        <el-card shadow="hover" class="resource-card">
          <div class="resource-icon">
            {{ typeIcon(res.resource_type) }}
          </div>
          <h4 class="resource-title">{{ res.title }}</h4>
          <p class="resource-desc">{{ res.description || '暂无描述' }}</p>
          <div class="resource-meta">
            <el-tag size="small">{{ res.resource_type_display }}</el-tag>
            <span v-if="res.category_name" class="meta-cat">{{ res.category_name }}</span>
          </div>
          <div class="resource-stats">
            <span>📥 {{ res.download_count }}</span>
            <span>{{ formatSize(res.file_size) }}</span>
          </div>
          <div class="resource-footer">
            <span class="uploader">{{ res.uploader_name }}</span>
            <span class="time">{{ res.created_at?.slice(0, 10) }}</span>
          </div>
          <div class="resource-actions">
            <el-button type="primary" size="small" @click="handleDownload(res)">下载</el-button>
            <el-button v-if="userStore.user?.id === res.uploader || userStore.isAdmin"
                       type="danger" size="small" @click="handleDeleteResource(res.id)">删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="!resources.length && !loading" description="暂无共享资料" />

    <!-- 分页 -->
    <div class="pagination" v-if="total > 20">
      <el-pagination v-model:current-page="page" :page-size="20" :total="total"
                     layout="prev, pager, next" @current-change="loadResources" />
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadVisible" title="上传共享资料" width="520px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="uploadForm.title" placeholder="资料标题" maxlength="200" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="简要描述..." />
        </el-form-item>
        <el-form-item label="文件" required>
          <el-upload ref="uploadRef" :auto-upload="false" :limit="1" :on-change="handleFileChange"
                     accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.txt">
            <el-button>选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 PDF、Word、PPT、Excel、压缩包等，最大 50MB</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="uploadForm.resource_type">
            <el-option label="PDF文档" value="pdf" />
            <el-option label="Word文档" value="doc" />
            <el-option label="PPT课件" value="ppt" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="uploadForm.category" placeholder="可选" clearable>
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.full_name || cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getResources, uploadResource, deleteResource, downloadResource, getCategoryFlat } from '../api/modules'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const resources = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const uploadVisible = ref(false)
const uploading = ref(false)

const filters = reactive({
  resource_type: '',
  category: '',
  search: '',
  ordering: '-created_at'
})

const uploadForm = reactive({
  title: '',
  description: '',
  file: null,
  resource_type: 'pdf',
  category: null
})

const typeIcon = (type) => ({ pdf: '📄', doc: '📝', ppt: '📊', other: '📁' }[type] || '📁')

const formatSize = (bytes) => {
  if (!bytes) return '未知'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(async () => {
  await loadResources()
  try {
    const res = await getCategoryFlat()
    categories.value = res.data.results || res.data || []
  } catch {}
})

const loadResources = async () => {
  loading.value = true
  try {
    const params = { page: page.value, ordering: filters.ordering }
    if (filters.resource_type) params.resource_type = filters.resource_type
    if (filters.category) params.category = filters.category
    if (filters.search) params.search = filters.search
    const res = await getResources(params)
    resources.value = res.data.results || res.data || []
    total.value = res.data.count || resources.value.length
  } catch {} finally {
    loading.value = false
  }
}

const handleFileChange = (file) => {
  uploadForm.file = file.raw
}

const submitUpload = async () => {
  if (!uploadForm.title.trim()) return ElMessage.warning('请输入标题')
  if (!uploadForm.file) return ElMessage.warning('请选择文件')
  uploading.value = true
  try {
    await uploadResource(uploadForm)
    ElMessage.success('上传成功')
    uploadVisible.value = false
    uploadForm.title = ''
    uploadForm.description = ''
    uploadForm.file = null
    await loadResources()
  } catch {} finally {
    uploading.value = false
  }
}

const handleDownload = async (res) => {
  try {
    await downloadResource(res.id)
  } catch {}
  // 打开文件下载
  window.open(res.file, '_blank')
}

const handleDeleteResource = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该资料？', '提示', { type: 'warning' })
    await deleteResource(id)
    ElMessage.success('已删除')
    await loadResources()
  } catch {}
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.filter-card { margin-bottom: 4px; }
.resource-card { margin-bottom: 16px; text-align: center; }
.resource-icon { font-size: 48px; margin: 12px 0; }
.resource-title { font-size: 15px; margin: 8px 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.resource-desc { color: #909399; font-size: 13px; height: 36px; overflow: hidden; margin-bottom: 8px; }
.resource-meta { display: flex; gap: 8px; justify-content: center; margin-bottom: 8px; }
.meta-cat { color: #909399; font-size: 12px; }
.resource-stats { display: flex; justify-content: space-around; color: #909399; font-size: 13px; margin-bottom: 8px; }
.resource-footer { display: flex; justify-content: space-between; color: #909399; font-size: 12px; margin-bottom: 12px; }
.resource-actions { display: flex; gap: 8px; justify-content: center; }
.pagination { display: flex; justify-content: center; margin-top: 20px; }
</style>
