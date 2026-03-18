<template>
  <div class="login-page">
    <div class="login-card">
      <h2 class="title">📚 校园教材共享平台</h2>
      <p class="subtitle">登录您的账户</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码"
                    prefix-icon="Lock" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="loading" native-type="submit">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="forgot-link">
        <router-link to="/forgot-password">忘记密码？</router-link>
      </div>
      <div class="footer-link">
        还没有账户？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (err) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
.title {
  text-align: center;
  font-size: 24px;
  color: #303133;
  margin-bottom: 8px;
}
.subtitle {
  text-align: center;
  color: #909399;
  margin-bottom: 30px;
}
.forgot-link {
  text-align: right;
  margin-top: -8px;
  margin-bottom: 12px;
}
.forgot-link a {
  color: #409eff;
  text-decoration: none;
  font-size: 13px;
}
.footer-link {
  text-align: center;
  margin-top: 16px;
  color: #909399;
}
.footer-link a {
  color: #409eff;
  text-decoration: none;
}
</style>
