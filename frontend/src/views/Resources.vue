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
        <el-col :span="4">
          <el-select v-model="filters.sale_type" placeholder="收费方式" clearable @change="loadResources">
            <el-option label="免费" value="free" />
            <el-option label="售卖" value="sell" />
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
            <el-tag size="small" :type="res.sale_type === 'sell' ? 'warning' : 'success'">
              {{ res.sale_type_display }}
            </el-tag>
            <span v-if="res.category_name" class="meta-cat">{{ res.category_name }}</span>
          </div>
          <div class="resource-price" v-if="res.sale_type === 'sell'">¥{{ res.price }}</div>
          <div class="resource-stats">
            <span>📥 {{ res.download_count }}</span>
            <span>{{ formatSize(res.file_size) }}</span>
          </div>
          <div class="resource-footer">
            <span class="uploader">{{ res.uploader_name }}</span>
            <span class="time">{{ res.created_at?.slice(0, 10) }}</span>
          </div>
          <div class="resource-actions">
            <el-button
              v-if="res.sale_type === 'sell' && !res.can_download"
              type="warning"
              size="small"
              @click="handleBuyResource(res)">
              {{ hasActiveOrder(res) ? '订单处理中' : '购买' }}
            </el-button>
            <el-button type="primary" size="small" :disabled="!res.can_download" @click="handleDownload(res)">下载</el-button>
            <el-button
              v-if="res.my_order_status === 'confirmed'"
              size="small"
              type="success"
              @click="handlePaid(res)">
              上传支付凭证
            </el-button>
            <el-button
              v-if="res.my_order_status === 'confirmed' && res.my_payment_qr"
              size="small"
              @click="showQr(res.my_payment_qr)">
              支付二维码
            </el-button>
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
        <el-form-item label="售卖方式">
          <el-radio-group v-model="uploadForm.sale_type">
            <el-radio value="free">免费共享</el-radio>
            <el-radio value="sell">售卖资料</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="价格" v-if="uploadForm.sale_type === 'sell'">
          <el-input-number v-model="uploadForm.price" :min="0.1" :precision="2" :step="1" />
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

    <el-dialog v-model="qrVisible" title="支付二维码" width="420px">
      <div style="text-align:center;">
        <img v-if="currentQr" :src="currentQr" style="max-width:100%;max-height:300px;" />
        <div v-else>暂无二维码</div>
      </div>
    </el-dialog>

    <el-dialog v-model="proofVisible" title="上传支付凭证" width="460px">
      <el-upload :auto-upload="false" :limit="1" :show-file-list="true" :on-change="handleProofChange" accept="image/*">
        <el-button>选择凭证图片</el-button>
      </el-upload>
      <template #footer>
        <el-button @click="proofVisible = false">取消</el-button>
        <el-button type="primary" @click="submitProof">提交凭证</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getResources, uploadResource, deleteResource, downloadResource, getCategoryFlat,
  createResourceOrder, completeResourceOrder
} from '../api/modules'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const resources = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const uploadVisible = ref(false)
const uploading = ref(false)
const qrVisible = ref(false)
const currentQr = ref('')
const proofVisible = ref(false)
const proofOrderId = ref(null)
const paymentProof = ref(null)

const filters = reactive({
  resource_type: '',
  category: '',
  sale_type: '',
  search: '',
  ordering: '-created_at'
})

const uploadForm = reactive({
  title: '',
  description: '',
  file: null,
  resource_type: 'pdf',
  sale_type: 'free',
  price: 0,
  category: null
})

const typeIcon = (type) => ({ pdf: '📄', doc: '📝', ppt: '📊', other: '📁' }[type] || '📁')
const ACTIVE_ORDER_STATUSES = ['pending', 'confirmed', 'paid_pending']
const hasActiveOrder = (res) => ACTIVE_ORDER_STATUSES.includes(res?.my_order_status)

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
    if (filters.sale_type) params.sale_type = filters.sale_type
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
    uploadForm.sale_type = 'free'
    uploadForm.price = 0
    await loadResources()
  } catch {} finally {
    uploading.value = false
  }
}

const handleDownload = async (res) => {
  if (!res.can_download) {
    return ElMessage.warning('请先完成资料支付流程')
  }
  try {
    const resp = await downloadResource(res.id)
    const fileUrl = resp?.data?.file || res.file
    if (!fileUrl) {
      return ElMessage.warning('文件链接不存在，请联系管理员')
    }
    window.open(fileUrl, '_blank')
  } catch {}
}

const handleBuyResource = async (res) => {
  if (!userStore.isLoggedIn) return ElMessage.warning('请先登录')
  if (hasActiveOrder(res)) return ElMessage.info('已有进行中的订单')
  try {
    await createResourceOrder({ resource_id: res.id })
    ElMessage.success('订单已创建，等待卖家确认并提供支付二维码')
    await loadResources()
  } catch {}
}

const handlePaid = async (res) => {
  if (!res.my_order_id) return
  proofOrderId.value = res.my_order_id
  paymentProof.value = null
  proofVisible.value = true
}

const handleProofChange = (file) => {
  paymentProof.value = file.raw
}

const submitProof = async () => {
  if (!proofOrderId.value) return
  if (!paymentProof.value) return ElMessage.warning('请先选择支付凭证图片')
  const formData = new FormData()
  formData.append('payment_proof', paymentProof.value)
  try {
    await completeResourceOrder(proofOrderId.value, formData)
    ElMessage.success('凭证已提交，等待卖家确认')
    proofVisible.value = false
    await loadResources()
  } catch {}
}

const showQr = (qr) => {
  currentQr.value = qr
  qrVisible.value = true
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
