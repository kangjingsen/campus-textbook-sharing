<template>
  <div class="wishlist-page">
    <div class="page-header">
      <h2>💖 我的心愿单</h2>
      <el-button type="primary" @click="openCreate">新增心愿</el-button>
    </div>

    <el-card>
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="title" label="书名" min-width="220" />
        <el-table-column prop="author" label="作者" width="140" />
        <el-table-column prop="isbn" label="ISBN" width="160" />
        <el-table-column prop="category_name" label="分类" width="180" />
        <el-table-column label="优先级" width="120">
          <template #default="{ row }">
            <el-rate v-model="row.priority" disabled :max="5" show-score text-color="#ff9900" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editItem(row)">编辑</el-button>
            <el-button size="small" type="success" v-if="row.status==='open'" @click="markMatched(row)">已匹配</el-button>
            <el-button size="small" type="danger" @click="deleteItem(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!items.length && !loading" description="还没有心愿，快添加吧" />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑心愿' : '新增心愿'" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="书名" required>
          <el-input v-model="form.title" maxlength="200" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="form.author" maxlength="200" />
        </el-form-item>
        <el-form-item label="ISBN">
          <el-input v-model="form.isbn" maxlength="20" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" clearable placeholder="可选">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.full_name || cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-rate v-model="form.priority" :max="5" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="待满足" value="open" />
            <el-option label="已匹配" value="matched" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createWishlistItem, deleteWishlistItem, getCategoryFlat, getWishlist, updateWishlistItem } from '../api/modules'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const items = ref([])
const categories = ref([])

const form = reactive({
  id: null,
  title: '',
  author: '',
  isbn: '',
  category: null,
  priority: 3,
  status: 'open',
  note: ''
})

const statusText = (s) => ({ open: '待满足', matched: '已匹配', closed: '已关闭' }[s] || s)
const statusType = (s) => ({ open: 'warning', matched: 'success', closed: 'info' }[s] || '')

const loadData = async () => {
  loading.value = true
  try {
    const [wRes, cRes] = await Promise.all([getWishlist(), getCategoryFlat()])
    items.value = wRes.data.results || wRes.data || []
    categories.value = cRes.data.results || cRes.data || []
  } catch {
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  Object.assign(form, {
    id: null,
    title: '',
    author: '',
    isbn: '',
    category: null,
    priority: 3,
    status: 'open',
    note: ''
  })
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const editItem = (row) => {
  Object.assign(form, {
    id: row.id,
    title: row.title,
    author: row.author,
    isbn: row.isbn,
    category: row.category,
    priority: row.priority,
    status: row.status,
    note: row.note
  })
  dialogVisible.value = true
}

const submit = async () => {
  if (!form.title.trim()) return ElMessage.warning('请输入书名')
  saving.value = true
  try {
    const payload = {
      title: form.title,
      author: form.author,
      isbn: form.isbn,
      category: form.category,
      priority: form.priority,
      status: form.status,
      note: form.note
    }
    if (form.id) {
      await updateWishlistItem(form.id, payload)
      ElMessage.success('已更新')
    } else {
      await createWishlistItem(payload)
      ElMessage.success('已添加')
    }
    dialogVisible.value = false
    await loadData()
  } catch {
  } finally {
    saving.value = false
  }
}

const markMatched = async (row) => {
  try {
    await updateWishlistItem(row.id, { status: 'matched' })
    ElMessage.success('已标记为匹配')
    await loadData()
  } catch {}
}

const deleteItem = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该心愿吗？', '提示', { type: 'warning' })
    await deleteWishlistItem(id)
    ElMessage.success('已删除')
    await loadData()
  } catch {}
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.page-header h2 { margin:0; }
</style>
