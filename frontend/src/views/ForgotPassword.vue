<template>
  <div class="forgot-page">
    <div class="forgot-card">
      <h2 class="title">找回密码</h2>
      <p class="subtitle">请输入用户名和注册邮箱，我们会发送密码重置链接。</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
        </el-form-item>
        <el-form-item label="注册邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入注册邮箱" size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="loading" native-type="submit">
            发送重置邮件
          </el-button>
        </el-form-item>
      </el-form>
      <div class="footer-link">
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { forgotPassword } from '../api/modules'

const formRef = ref(null)
const loading = ref(false)
const form = reactive({ username: '', email: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }]
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await forgotPassword(form)
    ElMessage.success('如果账号信息匹配，重置邮件已发送，请检查邮箱')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.forgot-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #5b8def 0%, #3fbf9b 100%);
}
.forgot-card {
  width: 440px;
  padding: 36px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.14);
}
.title { text-align: center; margin-bottom: 8px; }
.subtitle { text-align: center; color: #909399; margin-bottom: 24px; }
.footer-link { text-align: center; margin-top: 8px; }
.footer-link a { color: #409eff; text-decoration: none; }
</style>
