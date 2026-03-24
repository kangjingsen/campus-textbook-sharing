<template>
  <div class="review-manage">
    <h2>教材审核</h2>
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="待审核" name="pending">
        <el-table :data="reviewList" v-loading="loading" stripe>
          <el-table-column type="index" width="50" />
          <el-table-column label="教材名称" prop="textbook_title" min-width="180" />
          <el-table-column label="发布者" prop="owner_username" width="120" />
          <el-table-column label="交易类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.transaction_type === 'sell' ? '' : row.transaction_type === 'rent' ? 'warning' : 'success'" size="small">
                {{ { sell: '出售', rent: '租借', free: '赠送' }[row.transaction_type] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="价格" prop="price" width="80">
            <template #default="{ row }">¥{{ row.price }}</template>
          </el-table-column>
          <el-table-column label="敏感词检测" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.sensitive_words_found" type="danger" size="small">{{ row.sensitive_words_found }}</el-tag>
              <el-tag v-else type="success" size="small">无</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="提交时间" prop="created_at" width="170" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="handleReview(row, 'approved')">通过</el-button>
              <el-button type="danger" size="small" @click="openReject(row)">拒绝</el-button>
              <el-button link type="primary" size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="page"
          :page-size="20"
          :total="total"
          layout="total, prev, pager, next"
          style="margin-top: 16px;"
          @current-change="loadList"
        />
      </el-tab-pane>

      <el-tab-pane label="审核记录" name="records">
        <div class="record-filters">
          <el-select v-model="recordStatusFilter" clearable placeholder="审核结果" style="width: 140px;" @change="loadRecords">
            <el-option label="通过" value="approved" />
            <el-option label="驳回" value="rejected" />
          </el-select>
          <el-select v-model="recordAutoFilter" clearable placeholder="审核类型" style="width: 160px;" @change="loadRecords">
            <el-option label="自动审核" :value="true" />
            <el-option label="人工审核" :value="false" />
          </el-select>
        </div>

        <el-table :data="recordList" v-loading="recordLoading" stripe>
          <el-table-column type="index" width="50" />
          <el-table-column label="教材名称" prop="textbook_title" min-width="200" />
          <el-table-column label="审核结果" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'approved' ? 'success' : 'danger'" size="small">
                {{ row.status === 'approved' ? '通过' : '驳回' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="审核类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_auto ? 'warning' : 'info'" size="small">
                {{ row.is_auto ? '自动' : '人工' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="审核人" prop="reviewer_name" width="120" />
          <el-table-column label="审核意见" prop="reason" min-width="220" show-overflow-tooltip />
          <el-table-column label="命中敏感词" width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ row.sensitive_words_found || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="审核时间" prop="reviewed_at" width="180" />
        </el-table>

        <el-pagination
          v-model:current-page="recordPage"
          :page-size="20"
          :total="recordTotal"
          layout="total, prev, pager, next"
          style="margin-top: 16px;"
          @current-change="loadRecords"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 拒绝对话框 -->
    <el-dialog v-model="rejectDialogVisible" title="拒绝理由" width="400px">
      <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请输入拒绝理由" />
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="教材详情" width="600px">
      <el-descriptions :column="2" border v-if="detailItem">
        <el-descriptions-item label="标题">{{ detailItem.title }}</el-descriptions-item>
        <el-descriptions-item label="作者">{{ detailItem.author }}</el-descriptions-item>
        <el-descriptions-item label="ISBN">{{ detailItem.isbn }}</el-descriptions-item>
        <el-descriptions-item label="出版社">{{ detailItem.publisher }}</el-descriptions-item>
        <el-descriptions-item label="新旧程度">{{ detailItem.condition }}/5</el-descriptions-item>
        <el-descriptions-item label="价格">¥{{ detailItem.price }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ detailItem.description }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPendingReviews, getReviewRecords, reviewAction } from '../../api/modules'

const loading = ref(false)
const reviewList = ref([])
const page = ref(1)
const total = ref(0)
const activeTab = ref('pending')

const recordLoading = ref(false)
const recordList = ref([])
const recordPage = ref(1)
const recordTotal = ref(0)
const recordStatusFilter = ref('')
const recordAutoFilter = ref(null)

const rejectDialogVisible = ref(false)
const rejectReason = ref('')
const currentItem = ref(null)
const detailVisible = ref(false)
const detailItem = ref(null)

onMounted(() => loadList())

const handleTabChange = (tabName) => {
  if (tabName === 'records') {
    recordPage.value = 1
    loadRecords(true)
    return
  }
  page.value = 1
  loadList()
}

const loadList = async () => {
  if (activeTab.value !== 'pending') return
  loading.value = true
  try {
    const res = await getPendingReviews({ page: page.value })
    reviewList.value = res.data.results || res.data
    total.value = res.data.count || reviewList.value.length
  } catch {} finally { loading.value = false }
}

const loadRecords = async (force = false) => {
  if (!force && activeTab.value !== 'records') return
  recordLoading.value = true
  try {
    const params = { page: recordPage.value }
    if (recordStatusFilter.value) params.status = recordStatusFilter.value
    if (recordAutoFilter.value !== null) params.is_auto = recordAutoFilter.value
    const res = await getReviewRecords(params)
    recordList.value = res.data.results || res.data
    recordTotal.value = res.data.count || recordList.value.length
  } catch {} finally { recordLoading.value = false }
}

const handleReview = async (row, status) => {
  try {
    await ElMessageBox.confirm(`确定通过「${row.textbook_title}」的审核？`, '确认')
    await reviewAction(row.id, { status, reason: '审核通过' })
    ElMessage.success('操作成功')
    await Promise.all([loadList(), loadRecords(true)])
  } catch {}
}

const openReject = (row) => {
  currentItem.value = row
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

const submitReject = async () => {
  if (!rejectReason.value.trim()) return ElMessage.warning('请输入拒绝理由')
  try {
    await reviewAction(currentItem.value.id, { status: 'rejected', reason: rejectReason.value })
    ElMessage.success('已拒绝')
    rejectDialogVisible.value = false
    await Promise.all([loadList(), loadRecords(true)])
  } catch {}
}

const viewDetail = (row) => {
  detailItem.value = row
  detailVisible.value = true
}
</script>

<style scoped>
.review-manage h2 { margin-bottom: 20px; }
.record-filters { display: flex; gap: 12px; margin-bottom: 12px; }
</style>
