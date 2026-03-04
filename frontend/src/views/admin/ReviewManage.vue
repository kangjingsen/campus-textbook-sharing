<template>
  <div class="review-manage">
    <h2>教材审核</h2>
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

    <el-pagination v-model:current-page="page" :page-size="20"
                   :total="total" layout="total, prev, pager, next" style="margin-top: 16px;"
                   @current-change="loadList" />

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
import { getPendingReviews, reviewAction } from '../../api/modules'

const loading = ref(false)
const reviewList = ref([])
const page = ref(1)
const total = ref(0)
const rejectDialogVisible = ref(false)
const rejectReason = ref('')
const currentItem = ref(null)
const detailVisible = ref(false)
const detailItem = ref(null)

onMounted(() => loadList())

const loadList = async () => {
  loading.value = true
  try {
    const res = await getPendingReviews({ page: page.value })
    reviewList.value = res.data.results || res.data
    total.value = res.data.count || reviewList.value.length
  } catch {} finally { loading.value = false }
}

const handleReview = async (row, status) => {
  try {
    await ElMessageBox.confirm(`确定通过「${row.textbook_title}」的审核？`, '确认')
    await reviewAction(row.id, { status, reason: '审核通过' })
    ElMessage.success('操作成功')
    loadList()
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
    loadList()
  } catch {}
}

const viewDetail = (row) => {
  detailItem.value = row
  detailVisible.value = true
}
</script>

<style scoped>
.review-manage h2 { margin-bottom: 20px; }
</style>
