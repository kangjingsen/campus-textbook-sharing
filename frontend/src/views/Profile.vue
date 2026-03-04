<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="info-card">
          <div class="avatar-section">
            <el-upload :show-file-list="false" :before-upload="beforeAvatarUpload"
                       :http-request="uploadAvatar" accept="image/*">
              <el-avatar :size="100" :src="userStore.user?.avatar" />
              <div class="upload-tip">点击更换头像</div>
            </el-upload>
          </div>
          <div class="user-summary">
            <h3>{{ userStore.user?.username }}</h3>
            <p><el-icon><School /></el-icon> {{ userStore.user?.college || '未填写学院' }}</p>
            <p><el-icon><Reading /></el-icon> {{ userStore.user?.major || '未填写专业' }}</p>
            <el-tag :type="roleTagType">{{ roleLabel }}</el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="个人信息" name="profile">
              <el-form :model="profileForm" label-width="100px" style="max-width: 500px;">
                <el-form-item label="用户名">
                  <el-input v-model="profileForm.username" disabled />
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="profileForm.email" />
                </el-form-item>
                <el-form-item label="学号">
                  <el-input v-model="profileForm.student_id" />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="profileForm.phone" />
                </el-form-item>
                <el-form-item label="学院">
                  <el-input v-model="profileForm.college" />
                </el-form-item>
                <el-form-item label="专业">
                  <el-input v-model="profileForm.major" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveProfile" :loading="saving">保存修改</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="修改密码" name="password">
              <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef"
                       label-width="100px" style="max-width: 500px;">
                <el-form-item label="旧密码" prop="old_password">
                  <el-input v-model="pwdForm.old_password" type="password" show-password />
                </el-form-item>
                <el-form-item label="新密码" prop="new_password">
                  <el-input v-model="pwdForm.new_password" type="password" show-password />
                </el-form-item>
                <el-form-item label="确认密码" prop="confirm_password">
                  <el-input v-model="pwdForm.confirm_password" type="password" show-password />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="changePassword" :loading="changingPwd">修改密码</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="浏览记录" name="history">
              <el-table :data="historyList" v-loading="historyLoading" empty-text="暂无浏览记录">
                <el-table-column label="教材名称" prop="textbook_title" min-width="200" />
                <el-table-column label="浏览时间" prop="created_at" width="180" />
                <el-table-column label="操作" width="100">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="$router.push(`/textbooks/${row.textbook}`)">查看</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { School, Reading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { updateProfile, changePasswordApi, getBrowsingHistory } from '../api/modules'

const userStore = useUserStore()
const activeTab = ref('profile')
const saving = ref(false)
const changingPwd = ref(false)
const historyLoading = ref(false)
const historyList = ref([])
const pwdFormRef = ref(null)

const roleLabel = computed(() => {
  const map = { student: '学生', admin: '管理员', superadmin: '超级管理员' }
  return map[userStore.user?.role] || '学生'
})
const roleTagType = computed(() => {
  const map = { student: '', admin: 'warning', superadmin: 'danger' }
  return map[userStore.user?.role] || ''
})

const profileForm = reactive({
  username: '', email: '', student_id: '', phone: '', college: '', major: ''
})

const pwdForm = reactive({
  old_password: '', new_password: '', confirm_password: ''
})

const pwdRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少8个字符', trigger: 'blur' }],
  confirm_password: [{ required: true, message: '请确认密码', trigger: 'blur' },
    { validator: (_, v, cb) => v !== pwdForm.new_password ? cb(new Error('两次密码不一致')) : cb(), trigger: 'blur' }]
}

onMounted(() => {
  Object.assign(profileForm, userStore.user)
})

const saveProfile = async () => {
  saving.value = true
  try {
    const { username, ...data } = profileForm
    await updateProfile(data)
    await userStore.fetchProfile()
    ElMessage.success('保存成功')
  } catch {} finally { saving.value = false }
}

const changePassword = async () => {
  await pwdFormRef.value.validate()
  changingPwd.value = true
  try {
    await changePasswordApi(pwdForm)
    ElMessage.success('密码修改成功')
    Object.assign(pwdForm, { old_password: '', new_password: '', confirm_password: '' })
  } catch {} finally { changingPwd.value = false }
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    const res = await getBrowsingHistory()
    historyList.value = res.data.results || res.data
  } catch {} finally { historyLoading.value = false }
}

const beforeAvatarUpload = (file) => {
  const valid = file.type.startsWith('image/')
  if (!valid) ElMessage.error('请选择图片文件')
  return valid
}

const uploadAvatar = async ({ file }) => {
  const formData = new FormData()
  formData.append('avatar', file)
  try {
    await updateProfile(formData)
    await userStore.fetchProfile()
    ElMessage.success('头像更换成功')
  } catch {}
}

// 切换到浏览记录时自动加载
import { watch } from 'vue'
watch(activeTab, (val) => { if (val === 'history') loadHistory() })
</script>

<style scoped>
.profile-page { padding: 10px; }
.avatar-section { text-align: center; cursor: pointer; }
.upload-tip { font-size: 12px; color: #909399; margin-top: 8px; }
.user-summary { text-align: center; margin-top: 16px; }
.user-summary h3 { margin-bottom: 8px; }
.user-summary p { color: #606266; font-size: 14px; margin-bottom: 4px; display: flex; align-items: center; justify-content: center; gap: 4px; }
</style>
