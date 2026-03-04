<template>
  <div class="user-manage">
    <h2>用户管理</h2>

    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="6">
        <el-input v-model="searchKeyword" placeholder="搜索用户名/学号" clearable @clear="loadList" @keyup.enter="loadList" />
      </el-col>
      <el-col :span="4">
        <el-select v-model="roleFilter" placeholder="角色筛选" clearable @change="loadList">
          <el-option label="学生" value="student" />
          <el-option label="管理员" value="admin" />
          <el-option label="超级管理员" value="superadmin" />
        </el-select>
      </el-col>
      <el-col :span="2">
        <el-button type="primary" @click="loadList">搜索</el-button>
      </el-col>
    </el-row>

    <el-table :data="userList" v-loading="loading" stripe>
      <el-table-column type="index" width="50" />
      <el-table-column label="用户名" prop="username" width="120" />
      <el-table-column label="邮箱" prop="email" min-width="180" />
      <el-table-column label="学号" prop="student_id" width="120" />
      <el-table-column label="学院" prop="college" width="120" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'superadmin' ? 'danger' : row.role === 'admin' ? 'warning' : ''" size="small">
            {{ { student: '学生', admin: '管理员', superadmin: '超级管理员' }[row.role] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" prop="date_joined" width="170" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link :type="row.is_active ? 'danger' : 'success'" size="small" @click="toggleActive(row)">
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" :page-size="20"
                   :total="total" layout="total, prev, pager, next" style="margin-top: 16px;"
                   @current-change="loadList" />

    <!-- 编辑对话框 -->
    <el-dialog v-model="editVisible" title="编辑用户" width="450px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="editForm.username" disabled /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role">
            <el-option label="学生" value="student" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="editForm.is_active" active-text="正常" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAdminUserList, updateAdminUser } from '../../api/modules'

const loading = ref(false)
const userList = ref([])
const page = ref(1)
const total = ref(0)
const searchKeyword = ref('')
const roleFilter = ref('')
const editVisible = ref(false)
const editForm = reactive({ id: null, username: '', role: '', is_active: true })

onMounted(() => loadList())

const loadList = async () => {
  loading.value = true
  try {
    const params = { page: page.value }
    if (searchKeyword.value) params.search = searchKeyword.value
    if (roleFilter.value) params.role = roleFilter.value
    const res = await getAdminUserList(params)
    userList.value = res.data.results || res.data
    total.value = res.data.count || userList.value.length
  } catch {} finally { loading.value = false }
}

const openEdit = (row) => {
  Object.assign(editForm, { id: row.id, username: row.username, role: row.role, is_active: row.is_active })
  editVisible.value = true
}

const saveEdit = async () => {
  try {
    await updateAdminUser(editForm.id, { role: editForm.role, is_active: editForm.is_active })
    ElMessage.success('保存成功')
    editVisible.value = false
    loadList()
  } catch {}
}

const toggleActive = async (row) => {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${action}用户「${row.username}」？`, '确认')
    await updateAdminUser(row.id, { is_active: !row.is_active })
    ElMessage.success(`已${action}`)
    loadList()
  } catch {}
}
</script>

<style scoped>
.user-manage h2 { margin-bottom: 20px; }
</style>
