<template>
  <el-container class="layout">
    <!-- 顶部导航 -->
    <el-header class="header">
      <div class="header-left">
        <router-link to="/" class="logo">📚 教材共享</router-link>
        <el-menu mode="horizontal" :default-active="activeMenu" router :ellipsis="false" class="nav-menu">
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/textbooks">教材列表</el-menu-item>
          <el-menu-item v-if="userStore.isLoggedIn" index="/publish">发布教材</el-menu-item>
          <el-menu-item v-if="userStore.isLoggedIn" index="/orders">我的订单</el-menu-item>
          <el-menu-item index="/resources">在线资料</el-menu-item>
        </el-menu>
      </div>
      <div class="header-right">
        <!-- 搜索 -->
        <el-input v-model="searchKeyword" placeholder="搜索教材..." size="default"
                  style="width: 240px; margin-right: 16px;" @keyup.enter="handleSearch"
                  clearable>
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <template v-if="userStore.isLoggedIn">
          <!-- 消息 -->
          <el-badge :value="chatStore.unreadTotal" :hidden="!chatStore.unreadTotal" :max="99" class="msg-badge">
            <el-button :icon="ChatDotRound" circle @click="$router.push('/chat')" />
          </el-badge>

          <!-- 用户下拉 -->
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="userStore.user?.avatar" />
              <span class="username">{{ userStore.username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="my-textbooks">我的教材</el-dropdown-item>
                <el-dropdown-item v-if="userStore.isAdmin" command="admin" divided>管理后台</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" @click="$router.push('/login')">登录</el-button>
          <el-button @click="$router.push('/register')">注册</el-button>
        </template>
      </div>
    </el-header>

    <!-- 主内容 -->
    <el-main class="main-content">
      <router-view />
    </el-main>

    <!-- 底部 -->
    <el-footer class="footer">
      <p>© 2026 校园教材共享平台 | 让知识流动起来</p>
    </el-footer>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useChatStore } from '../stores/chat'
import { Search, ChatDotRound } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const chatStore = useChatStore()
const searchKeyword = ref('')

const activeMenu = computed(() => route.path)

onMounted(() => {
  if (userStore.isLoggedIn) {
    chatStore.fetchUnreadCount()
    // 每30秒检查一次未读
    setInterval(() => chatStore.fetchUnreadCount(), 30000)
  }
})

watch(() => userStore.isLoggedIn, (val) => {
  if (val) chatStore.fetchUnreadCount()
})

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/textbooks', query: { q: searchKeyword.value.trim() } })
  }
}

const handleCommand = (cmd) => {
  switch (cmd) {
    case 'profile': router.push('/profile'); break
    case 'my-textbooks': router.push('/my-textbooks'); break
    case 'admin': router.push('/admin'); break
    case 'logout':
      userStore.logout()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.layout { min-height: 100vh; }
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  padding: 0 24px;
  z-index: 100;
}
.header-left { display: flex; align-items: center; }
.logo {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  text-decoration: none;
  margin-right: 24px;
  white-space: nowrap;
}
.nav-menu { border-bottom: none; }
.header-right { display: flex; align-items: center; gap: 12px; }
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.username { font-size: 14px; color: #303133; }
.msg-badge { margin-right: 4px; }
.main-content {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}
.footer {
  text-align: center;
  color: #909399;
  font-size: 14px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}
</style>
