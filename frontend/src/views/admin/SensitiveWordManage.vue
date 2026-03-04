<template>
  <div class="sensitive-word-manage">
    <h2>敏感词管理</h2>

    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="4">
        <el-select v-model="categoryFilter" placeholder="分类筛选" clearable @change="loadList">
          <el-option label="政治" value="political" />
          <el-option label="暴力" value="violence" />
          <el-option label="违法" value="illegal" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-col>
      <el-col :span="4">
        <el-button type="primary" @click="openAdd">添加敏感词</el-button>
      </el-col>
      <el-col :span="4">
        <el-button @click="openBatchAdd">批量添加</el-button>
      </el-col>
    </el-row>

    <el-table :data="wordList" v-loading="loading" stripe>
      <el-table-column type="index" width="50" />
      <el-table-column label="敏感词" prop="word" min-width="200" />
      <el-table-column label="分类" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ { political: '政治', violence: '暴力', illegal: '违法', other: '其他' }[row.category] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="created_at" width="170" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEditWord(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteWord(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" :page-size="20"
                   :total="total" layout="total, prev, pager, next" style="margin-top: 16px;"
                   @current-change="loadList" />

    <!-- 添加/编辑 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑敏感词' : '添加敏感词'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="敏感词"><el-input v-model="form.word" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category">
            <el-option label="政治" value="political" />
            <el-option label="暴力" value="violence" />
            <el-option label="违法" value="illegal" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveWord">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量添加 -->
    <el-dialog v-model="batchVisible" title="批量添加敏感词" width="500px">
      <el-form label-width="80px">
        <el-form-item label="分类">
          <el-select v-model="batchCategory">
            <el-option label="政治" value="political" />
            <el-option label="暴力" value="violence" />
            <el-option label="违法" value="illegal" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="词汇">
          <el-input v-model="batchWords" type="textarea" :rows="5" placeholder="每行一个敏感词" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBatch">批量添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSensitiveWordList, createSensitiveWord, updateSensitiveWord, deleteSensitiveWord } from '../../api/modules'

const loading = ref(false)
const wordList = ref([])
const page = ref(1)
const total = ref(0)
const categoryFilter = ref('')
const dialogVisible = ref(false)
const batchVisible = ref(false)
const isEdit = ref(false)
const form = reactive({ id: null, word: '', category: 'other' })
const batchCategory = ref('other')
const batchWords = ref('')

onMounted(() => loadList())

const loadList = async () => {
  loading.value = true
  try {
    const params = { page: page.value }
    if (categoryFilter.value) params.category = categoryFilter.value
    const res = await getSensitiveWordList(params)
    wordList.value = res.data.results || res.data
    total.value = res.data.count || wordList.value.length
  } catch {} finally { loading.value = false }
}

const openAdd = () => {
  isEdit.value = false
  Object.assign(form, { id: null, word: '', category: 'other' })
  dialogVisible.value = true
}

const openEditWord = (row) => {
  isEdit.value = true
  Object.assign(form, { id: row.id, word: row.word, category: row.category })
  dialogVisible.value = true
}

const saveWord = async () => {
  if (!form.word.trim()) return ElMessage.warning('请输入敏感词')
  try {
    if (isEdit.value) {
      await updateSensitiveWord(form.id, { word: form.word, category: form.category })
    } else {
      await createSensitiveWord({ word: form.word, category: form.category })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadList()
  } catch {}
}

const deleteWord = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除敏感词「${row.word}」？`, '确认')
    await deleteSensitiveWord(row.id)
    ElMessage.success('删除成功')
    loadList()
  } catch {}
}

const openBatchAdd = () => {
  batchWords.value = ''
  batchCategory.value = 'other'
  batchVisible.value = true
}

const saveBatch = async () => {
  const words = batchWords.value.split('\n').map(w => w.trim()).filter(Boolean)
  if (!words.length) return ElMessage.warning('请输入至少一个敏感词')
  try {
    for (const word of words) {
      await createSensitiveWord({ word, category: batchCategory.value })
    }
    ElMessage.success(`成功添加 ${words.length} 个敏感词`)
    batchVisible.value = false
    loadList()
  } catch {}
}
</script>

<style scoped>
.sensitive-word-manage h2 { margin-bottom: 20px; }
</style>
