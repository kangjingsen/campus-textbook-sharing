<template>
  <div class="orders-page">
    <el-card>
      <template #header>
        <h2>
          📋 我的订单
          <el-tag v-if="orderNotifyCount > 0" type="danger" effect="dark" size="small" style="margin-left: 8px;">
            待处理 {{ orderNotifyCount }}
          </el-tag>
        </h2>
      </template>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <el-tabs v-model="activeRole" @tab-change="loadOrders" style="flex: 1;">
          <el-tab-pane label="全部" name="all" />
          <el-tab-pane label="我买的" name="buyer" :disabled="viewAllOrders" />
          <el-tab-pane label="我卖的" name="seller" :disabled="viewAllOrders" />
        </el-tabs>
        <el-button
          v-if="canViewAllOrders"
          size="small"
          :type="viewAllOrders ? 'primary' : 'default'"
          @click="toggleAllOrdersView"
          style="margin-left: 12px; margin-bottom: 8px;">
          {{ viewAllOrders ? '退出全站视图' : '查看全站订单' }}
        </el-button>
      </div>

      <el-alert
        v-if="viewAllOrders"
        title="全站订单只读视图：仅查看状态，不可执行取消/确认/完成操作"
        type="info"
        :closable="false"
        style="margin-bottom: 12px;"
      />

      <el-radio-group v-model="statusFilter" size="small" @change="loadOrders" style="margin-bottom: 16px;">
        <el-radio-button value="">全部状态</el-radio-button>
        <el-radio-button value="pending">待确认</el-radio-button>
        <el-radio-button value="confirmed">已确认</el-radio-button>
        <el-radio-button value="completed">已完成</el-radio-button>
        <el-radio-button value="cancelled">已取消</el-radio-button>
      </el-radio-group>

      <el-table :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="160" />
        <el-table-column label="教材" min-width="200">
          <template #default="{ row }">
            <span style="cursor: pointer; color: #409eff;"
                  @click="$router.push(`/textbooks/${row.textbook}`)">
              {{ row.textbook_title }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="对方" width="120">
          <template #default="{ row }">
            {{ row.buyer === userStore.user?.id ? row.seller_name : row.buyer_name }}
          </template>
        </el-table-column>
        <el-table-column label="价格" width="100">
          <template #default="{ row }">
            <span class="price">¥{{ row.price }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column v-if="!viewAllOrders" label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <!-- 卖方操作 -->
            <template v-if="row.seller === userStore.user?.id">
              <el-button v-if="row.status === 'pending'" type="primary" size="small"
                         @click="handleConfirm(row.id)">确认</el-button>
            </template>
            <!-- 双方都可操作 -->
            <el-button v-if="row.status === 'confirmed'" type="success" size="small"
                       @click="handleComplete(row.id)">完成交易</el-button>
            <el-button v-if="['pending', 'confirmed'].includes(row.status)" type="danger" size="small"
                       @click="handleCancel(row.id)">取消</el-button>
            <el-button v-if="row.status === 'completed' && row.transaction_type === 'rent' && row.buyer === userStore.user?.id"
                       size="small" @click="handleReturn(row.id)">归还</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="total > 0">
        <el-pagination v-model:current-page="page" :page-size="20" :total="total"
                       layout="prev, pager, next, total" @current-change="loadOrders" />
      </div>
    </el-card>

    <el-card style="margin-top: 16px;">
      <template #header><h3>📂 资料订单</h3></template>
      <el-table :data="resourceOrders" v-loading="resourceLoading" stripe>
        <el-table-column prop="id" label="订单ID" width="100" />
        <el-table-column prop="resource_title" label="资料" min-width="220" />
        <el-table-column label="对方" width="120">
          <template #default="{ row }">
            {{ row.buyer === userStore.user?.id ? row.seller_name : row.buyer_name }}
          </template>
        </el-table-column>
        <el-table-column label="价格" width="100">
          <template #default="{ row }">¥{{ row.price }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="!viewAllOrders" label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.seller === userStore.user?.id && row.status === 'pending'"
              size="small"
              type="primary"
              @click="handleConfirmResource(row.id)">
              确认并上传二维码
            </el-button>
            <el-button
              v-if="row.buyer === userStore.user?.id && row.status === 'confirmed' && (row.payment_qr_image || row.payment_qr)"
              size="small"
              @click="showQr(row.payment_qr_image || row.payment_qr)">
              查看支付码
            </el-button>
            <el-button
              v-if="row.buyer === userStore.user?.id && row.status === 'confirmed'"
              size="small"
              type="success"
              @click="handleCompleteResource(row.id)">
              上传支付凭证
            </el-button>
            <el-button
              v-if="row.seller === userStore.user?.id && row.status === 'paid_pending'"
              size="small"
              type="primary"
              @click="handleSellerCompleteResource(row.id)">
              确认收款
            </el-button>
            <el-button
              v-if="['pending','confirmed'].includes(row.status)"
              size="small"
              type="danger"
              @click="handleCancelResource(row.id)">
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="qrVisible" title="支付二维码" width="420px">
      <div style="text-align: center;">
        <img v-if="currentQr" :src="currentQr" style="max-width: 100%; max-height: 320px;" />
        <div v-else>暂无二维码</div>
      </div>
    </el-dialog>

    <el-dialog v-model="cancelDialogVisible" title="取消订单原因" width="420px">
      <el-form label-width="90px">
        <el-form-item label="订单类型">
          <span>{{ cancelTargetType === 'resource' ? '资料订单' : '教材订单' }}</span>
        </el-form-item>
        <el-form-item label="取消原因" required>
          <el-select v-model="cancelReason" placeholder="请选择取消原因" style="width: 100%;">
            <el-option
              v-for="item in cancelReasonOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialogVisible = false">返回</el-button>
        <el-button type="danger" @click="submitCancel" :loading="cancelSubmitting">确认取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getOrders, confirmOrder, completeOrder, cancelOrder, returnOrder,
  getResourceOrders, confirmResourceOrder, completeResourceOrder, sellerCompleteResourceOrder, cancelResourceOrder
} from '../api/modules'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const orders = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const activeRole = ref('all')
const statusFilter = ref('')
const viewAllOrders = ref(false)
const resourceOrders = ref([])
const resourceLoading = ref(false)
const orderNotifyCount = ref(0)
const qrVisible = ref(false)
const currentQr = ref('')
const cancelDialogVisible = ref(false)
const cancelSubmitting = ref(false)
const cancelTargetId = ref(null)
const cancelTargetType = ref('textbook')
const cancelReason = ref('')
const cancelReasonOptions = [
  { value: 'price', label: '价格不合适' },
  { value: 'schedule', label: '无法线下交易' },
  { value: 'duplicate', label: '重复下单' },
  { value: 'not_needed', label: '暂时不需要' },
  { value: 'unresponsive', label: '对方长时间未响应' },
  { value: 'other', label: '其他' }
]
let pollTimer = null

const canViewAllOrders = computed(() => ['admin', 'superadmin'].includes(userStore.user?.role || ''))

const getStatusTag = (s) => ({
  pending: 'warning', confirmed: '', completed: 'success',
  paid_pending: 'warning', cancelled: 'info', returned: 'success'
}[s] || '')

onMounted(async () => {
  await loadOrders()
  await loadResourceOrders()
  await loadOrderNotifications()
  pollTimer = setInterval(() => {
    loadOrderNotifications()
  }, 30000)
})

onBeforeUnmount(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})

const extractCount = (payload) => {
  if (payload && typeof payload.count === 'number') return payload.count
  if (Array.isArray(payload)) return payload.length
  if (payload?.results && Array.isArray(payload.results)) return payload.results.length
  return 0
}

const loadOrderNotifications = async () => {
  try {
    const [orderRes, resourceRes] = await Promise.all([
      getOrders({ role: 'seller', status: 'pending', page: 1 }),
      getResourceOrders({ role: 'seller', status: 'pending' })
    ])
    const textbookPending = extractCount(orderRes.data)
    const resourcePending = extractCount(resourceRes.data)
    orderNotifyCount.value = textbookPending + resourcePending
  } catch {
    orderNotifyCount.value = 0
  }
}

const loadOrders = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      role: viewAllOrders.value ? 'all' : activeRole.value
    }
    if (viewAllOrders.value) params.all_users = 1
    if (statusFilter.value) params.status = statusFilter.value
    const res = await getOrders(params)
    orders.value = res.data.results || res.data
    total.value = res.data.count || orders.value.length
  } catch {} finally {
    loading.value = false
  }
  await loadResourceOrders()
  loadOrderNotifications()
}

const handleConfirm = async (id) => {
  await ElMessageBox.confirm('确认接受订单？', '提示')
  await confirmOrder(id)
  ElMessage.success('已确认')
  loadOrders()
}

const handleComplete = async (id) => {
  await ElMessageBox.confirm('确认交易完成？', '提示')
  await completeOrder(id)
  ElMessage.success('交易完成')
  loadOrders()
}

const handleCancel = async (id) => {
  cancelTargetType.value = 'textbook'
  cancelTargetId.value = id
  cancelReason.value = ''
  cancelDialogVisible.value = true
}

const handleReturn = async (id) => {
  await ElMessageBox.confirm('确认已归还教材？', '提示')
  await returnOrder(id)
  ElMessage.success('已归还')
  loadOrders()
}

const loadResourceOrders = async () => {
  resourceLoading.value = true
  try {
    const params = {
      role: viewAllOrders.value ? 'all' : (activeRole.value === 'all' ? undefined : activeRole.value)
    }
    if (viewAllOrders.value) params.all_users = 1
    const res = await getResourceOrders(params)
    resourceOrders.value = res.data.results || res.data || []
  } catch {} finally {
    resourceLoading.value = false
  }
}

const toggleAllOrdersView = async () => {
  viewAllOrders.value = !viewAllOrders.value
  page.value = 1
  activeRole.value = 'all'
  await loadOrders()
}

const handleConfirmResource = async (id) => {
  try {
    await ElMessageBox.confirm('请选择支付二维码图片后提交。', '确认资料订单')
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = async () => {
      const file = input.files && input.files[0]
      if (!file) return
      const formData = new FormData()
      formData.append('payment_qr_image', file)
      await confirmResourceOrder(id, formData)
      ElMessage.success('已确认并发送支付二维码')
      await loadResourceOrders()
      loadOrderNotifications()
    }
    input.click()
  } catch {}
}

const handleCompleteResource = async (id) => {
  try {
    await ElMessageBox.confirm('请选择支付凭证图片后提交，提交后将等待卖家确认收款。', '上传支付凭证')
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = async () => {
      const file = input.files && input.files[0]
      if (!file) return
      const formData = new FormData()
      formData.append('payment_proof', file)
      await completeResourceOrder(id, formData)
      ElMessage.success('凭证已提交，等待卖家确认')
      await loadResourceOrders()
      loadOrderNotifications()
    }
    input.click()
  } catch {}
}

const handleSellerCompleteResource = async (id) => {
  try {
    await ElMessageBox.confirm('确认已收款并完成该资料订单？', '提示')
    await sellerCompleteResourceOrder(id)
    ElMessage.success('订单完成，买家已可下载')
    await loadResourceOrders()
    loadOrderNotifications()
  } catch {}
}

const handleCancelResource = async (id) => {
  cancelTargetType.value = 'resource'
  cancelTargetId.value = id
  cancelReason.value = ''
  cancelDialogVisible.value = true
}

const submitCancel = async () => {
  if (!cancelReason.value) {
    ElMessage.warning('请选择取消原因')
    return
  }
  if (!cancelTargetId.value) return

  cancelSubmitting.value = true
  try {
    if (cancelTargetType.value === 'resource') {
      await cancelResourceOrder(cancelTargetId.value, { reason: cancelReason.value })
      await loadResourceOrders()
    } else {
      await cancelOrder(cancelTargetId.value, { reason: cancelReason.value })
      await loadOrders()
    }
    ElMessage.success('已取消')
    cancelDialogVisible.value = false
    loadOrderNotifications()
  } catch {
  } finally {
    cancelSubmitting.value = false
  }
}

const showQr = (qr) => {
  currentQr.value = qr || ''
  qrVisible.value = true
}
</script>

<style scoped>
.price { color: #f56c6c; font-weight: bold; }
.pagination { text-align: center; margin-top: 16px; }
</style>
