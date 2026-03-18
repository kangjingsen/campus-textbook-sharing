<template>
  <div class="reset-page">
    <div class="reset-card">
      <h2 class="title">重置密码</h2>
      <p class="subtitle">请输入新密码并确认。</p>

      <el-alert
        v-if="invalidLink"
        type="error"
        :closable="false"
        title="重置链接无效，请重新发起忘记密码。"
        style="margin-bottom: 16px;"
      />

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="form.new_password" type="password" show-password placeholder="请输入新密码" size="large" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="new_password_confirm">
          <el-input v-model="form.new_password_confirm" type="password" show-password placeholder="请再次输入新密码" size="large" />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :disabled="invalidLink"
            :loading="loading"
            native-type="submit">
            提交新密码
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
import { ref, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resetPassword } from '../api/modules'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const uid = computed(() => String(route.query.uid || ''))
const token = computed(() => String(route.query.token || ''))
const invalidLink = computed(() => !uid.value || !token.value)

const form = reactive({
  new_password: '',
  new_password_confirm: ''
})

const rules = {
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
  new_password_confirm: [{ required: true, message: '请再次输入新密码', trigger: 'blur' }]
}

const handleSubmit = async () => {
  if (invalidLink.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await resetPassword({
      uid: uid.value,
      token: token.value,
      new_password: form.new_password,
      new_password_confirm: form.new_password_confirm
    })
    ElMessage.success('密码重置成功，请使用新密码登录')
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.reset-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4f81e2 0%, #66c2a5 100%);
}
.reset-card {
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
