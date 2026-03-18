<template>
  <div class="dashboard">
    <h2>数据概览</h2>

    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" :style="{ background: card.color }">
              <el-icon :size="28"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ card.value }}</div>
              <div class="stat-label">{{ card.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card header="交易类型分布">
          <div ref="pieRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="月度流通趋势">
          <div ref="lineRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card header="热门教材 TOP 10">
          <el-table :data="popularList" stripe>
            <el-table-column type="index" width="50" />
            <el-table-column label="教材名称" prop="title" min-width="200" />
            <el-table-column label="作者" prop="author" width="120" />
            <el-table-column label="浏览量" prop="view_count" width="100" sortable />
            <el-table-column label="订单数" prop="order_count" width="100" sortable />
            <el-table-column label="完成单" prop="completed_order_count" width="100" sortable />
            <el-table-column label="取消单" prop="cancelled_order_count" width="100" sortable />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, markRaw } from 'vue'
import * as echarts from 'echarts'
import { Reading, User, ShoppingCart, DataBoard } from '@element-plus/icons-vue'
import { getDashboardOverview, getTransactionTypeDist, getCirculationRate, getPopularTextbookRank } from '../../api/modules'

const overview = ref({})
const popularList = ref([])
const pieRef = ref(null)
const lineRef = ref(null)

const statCards = computed(() => [
  { label: '教材总数', value: overview.value.textbook_count || 0, icon: markRaw(Reading), color: '#409eff' },
  { label: '用户总数', value: overview.value.user_count || 0, icon: markRaw(User), color: '#67c23a' },
  { label: '订单总数', value: overview.value.order_count || 0, icon: markRaw(ShoppingCart), color: '#e6a23c' },
  { label: '待审核', value: overview.value.pending_review_count || 0, icon: markRaw(DataBoard), color: '#f56c6c' },
])

onMounted(async () => {
  try {
    const [overviewRes, pieRes, lineRes, rankRes] = await Promise.all([
      getDashboardOverview(),
      getTransactionTypeDist(),
      getCirculationRate(),
      getPopularTextbookRank()
    ])

    overview.value = overviewRes.data
    popularList.value = (rankRes.data.results || rankRes.data).slice(0, 10)

    // 饼图
    const pieChart = echarts.init(pieRef.value)
    const pieData = pieRes.data
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: [
          { value: pieData.sell || 0, name: '出售' },
          { value: pieData.rent || 0, name: '租借' },
          { value: pieData.free || 0, name: '赠送' }
        ],
        emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' } }
      }]
    })

    // 折线图
    const lineChart = echarts.init(lineRef.value)
    const lineData = Array.isArray(lineRes.data) ? lineRes.data : []
    lineChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: lineData.map(i => i.month) },
      yAxis: { type: 'value' },
      series: [{ data: lineData.map(i => i.count), type: 'line', smooth: true, areaStyle: { opacity: 0.3 } }]
    })

    window.addEventListener('resize', () => { pieChart.resize(); lineChart.resize() })
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.dashboard h2 { margin-bottom: 20px; }
.stat-card { display: flex; align-items: center; gap: 16px; }
.stat-icon {
  width: 56px; height: 56px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; color: #fff;
}
.stat-value { font-size: 28px; font-weight: bold; }
.stat-label { color: #909399; font-size: 14px; }
</style>
