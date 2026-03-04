<template>
  <div class="orders-page">
    <el-card>
      <template #header><h2>📋 我的订单</h2></template>

      <el-tabs v-model="activeRole" @tab-change="loadOrders">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="我买的" name="buyer" />
        <el-tab-pane label="我卖的" name="seller" />
      </el-tabs>

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
        <el-table-column label="操作" width="200" fixed="right">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getOrders, confirmOrder, completeOrder, cancelOrder, returnOrder } from '../api/modules'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const orders = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const activeRole = ref('all')
const statusFilter = ref('')

const getStatusTag = (s) => ({
  pending: 'warning', confirmed: '', completed: 'success',
  cancelled: 'info', returned: 'success'
}[s] || '')

onMounted(() => loadOrders())

const loadOrders = async () => {
  loading.value = true
  try {
    const params = { page: page.value, role: activeRole.value }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await getOrders(params)
    orders.value = res.data.results || res.data
    total.value = res.data.count || orders.value.length
  } catch {} finally {
    loading.value = false
  }
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
  await ElMessageBox.confirm('确认取消订单？', '提示', { type: 'warning' })
  await cancelOrder(id)
  ElMessage.success('已取消')
  loadOrders()
}

const handleReturn = async (id) => {
  await ElMessageBox.confirm('确认已归还教材？', '提示')
  await returnOrder(id)
  ElMessage.success('已归还')
  loadOrders()
}
</script>

<style scoped>
.price { color: #f56c6c; font-weight: bold; }
.pagination { text-align: center; margin-top: 16px; }
</style>
