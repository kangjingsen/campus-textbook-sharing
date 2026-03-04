<template>
  <div class="admin-layout">
    <el-container>
      <el-aside width="220px">
        <div class="admin-logo">📚 管理后台</div>
        <el-menu :default-active="activeMenu" router class="admin-menu">
          <el-menu-item index="/admin/dashboard">
            <el-icon><DataBoard /></el-icon>数据概览
          </el-menu-item>
          <el-menu-item index="/admin/reviews">
            <el-icon><Document /></el-icon>教材审核
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>用户管理
          </el-menu-item>
          <el-menu-item index="/admin/categories">
            <el-icon><Menu /></el-icon>分类管理
          </el-menu-item>
          <el-menu-item index="/admin/sensitive-words">
            <el-icon><Warning /></el-icon>敏感词管理
          </el-menu-item>
          <el-menu-item index="/admin/statistics">
            <el-icon><TrendCharts /></el-icon>统计分析
          </el-menu-item>
        </el-menu>
        <div class="back-link">
          <el-button link @click="$router.push('/')">← 返回前台</el-button>
        </div>
      </el-aside>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataBoard, Document, User, Menu, Warning, TrendCharts } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.admin-layout { height: 100vh; }
.el-container { height: 100%; }
.el-aside { background: #304156; overflow: hidden; display: flex; flex-direction: column; }
.admin-logo {
  height: 60px; display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 18px; font-weight: bold;
}
.admin-menu {
  border-right: none; background: #304156; flex: 1;
}
.admin-menu .el-menu-item { color: #bfcbd9; }
.admin-menu .el-menu-item:hover { background: #263445; }
.admin-menu .el-menu-item.is-active { color: #409eff; background: #263445; }
.back-link { padding: 16px; text-align: center; }
.back-link .el-button { color: #bfcbd9; }
.admin-main { background: #f0f2f5; }
</style>
