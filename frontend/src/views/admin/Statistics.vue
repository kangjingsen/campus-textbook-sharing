<template>
  <div class="statistics-page">
    <h2>统计分析</h2>

    <!-- 流通率趋势 -->
    <el-card header="教材流通率月度趋势" style="margin-bottom: 20px;">
      <div ref="circulationRef" style="height: 350px;"></div>
    </el-card>

    <el-row :gutter="16" style="margin-bottom: 20px;">
      <!-- 价格趋势 -->
      <el-col :span="12">
        <el-card header="各类别平均价格趋势">
          <div ref="priceRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <!-- 学院需求 -->
      <el-col :span="12">
        <el-card header="各学院需求分布">
          <div ref="collegeRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 20px;">
      <!-- 交易类型分布 -->
      <el-col :span="8">
        <el-card header="交易类型占比">
          <div ref="txTypeRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <!-- 分类分布 -->
      <el-col :span="8">
        <el-card header="教材分类分布">
          <div ref="categoryRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <!-- 用户活跃度 -->
      <el-col :span="8">
        <el-card header="用户活跃度">
          <div ref="activityRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 热门排行 -->
    <el-card header="热门教材排行">
      <el-radio-group v-model="rankType" style="margin-bottom: 12px;" @change="loadRank">
        <el-radio-button value="views">按浏览量</el-radio-button>
        <el-radio-button value="orders">按订单数</el-radio-button>
        <el-radio-button value="comprehensive">综合排行</el-radio-button>
      </el-radio-group>
      <div ref="rankRef" style="height: 350px;"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import {
  getCirculationRate, getPriceTrend, getCollegeDemand,
  getTransactionTypeDist, getCategoryDistribution,
  getUserActivity, getPopularTextbookRank
} from '../../api/modules'

const circulationRef = ref(null)
const priceRef = ref(null)
const collegeRef = ref(null)
const txTypeRef = ref(null)
const categoryRef = ref(null)
const activityRef = ref(null)
const rankRef = ref(null)
const rankType = ref('views')
const charts = []

const initChart = (domRef) => {
  const chart = echarts.init(domRef)
  charts.push(chart)
  return chart
}

onMounted(async () => {
  try {
    const [cirRes, priceRes, collegeRes, txRes, catRes, actRes] = await Promise.all([
      getCirculationRate(), getPriceTrend(), getCollegeDemand(),
      getTransactionTypeDist(), getCategoryDistribution(), getUserActivity()
    ])

    // 流通率趋势 - 折线
    const cirChart = initChart(circulationRef.value)
    const cirData = Array.isArray(cirRes.data) ? cirRes.data : []
    cirChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: cirData.map(i => i.month) },
      yAxis: { type: 'value', name: '流通量' },
      series: [{
        data: cirData.map(i => i.count), type: 'line', smooth: true,
        areaStyle: { opacity: 0.3 }, itemStyle: { color: '#409eff' }
      }],
      grid: { left: 60, right: 20, top: 30, bottom: 30 }
    })

    // 价格趋势 - 多线
    const priceChart = initChart(priceRef.value)
    const priceData = Array.isArray(priceRes.data) ? priceRes.data : []
    const categories = [...new Set(priceData.map(i => i.category))]
    const months = [...new Set(priceData.map(i => i.month))]
    priceChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: categories, bottom: 0 },
      xAxis: { type: 'category', data: months },
      yAxis: { type: 'value', name: '平均价格(¥)' },
      series: categories.map(cat => ({
        name: cat, type: 'line', smooth: true,
        data: months.map(m => {
          const item = priceData.find(p => p.category === cat && p.month === m)
          return item ? item.avg_price : 0
        })
      })),
      grid: { left: 60, right: 20, top: 30, bottom: 40 }
    })

    // 学院需求 - 柱状
    const collegeChart = initChart(collegeRef.value)
    const collegeData = Array.isArray(collegeRes.data) ? collegeRes.data : []
    collegeChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: collegeData.map(i => i.college), axisLabel: { rotate: 30 } },
      yAxis: { type: 'value' },
      series: [{ data: collegeData.map(i => i.count), type: 'bar', itemStyle: { color: '#67c23a' } }],
      grid: { left: 50, right: 20, top: 20, bottom: 60 }
    })

    // 交易类型 - 饼图
    const txChart = initChart(txTypeRef.value)
    const txData = txRes.data || {}
    txChart.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['35%', '65%'],
        data: [
          { value: txData.sell || 0, name: '出售', itemStyle: { color: '#409eff' } },
          { value: txData.rent || 0, name: '租借', itemStyle: { color: '#e6a23c' } },
          { value: txData.free || 0, name: '赠送', itemStyle: { color: '#67c23a' } }
        ]
      }]
    })

    // 分类分布 - 饼图
    const catChart = initChart(categoryRef.value)
    const catData = Array.isArray(catRes.data) ? catRes.data : []
    catChart.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: '65%',
        data: catData.map(i => ({ value: i.count, name: i.category }))
      }]
    })

    // 用户活跃度 - 柱状
    const actChart = initChart(activityRef.value)
    const actData = Array.isArray(actRes.data) ? actRes.data : []
    actChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: actData.map(i => i.date), axisLabel: { rotate: 45 } },
      yAxis: { type: 'value', name: '活跃用户数' },
      series: [{ data: actData.map(i => i.count), type: 'bar', itemStyle: { color: '#e6a23c' } }],
      grid: { left: 50, right: 20, top: 30, bottom: 60 }
    })

    // 热门排行
    await loadRank()

    window.addEventListener('resize', resizeAll)
  } catch (e) { console.error(e) }
})

const loadRank = async () => {
  try {
    const res = await getPopularTextbookRank({ type: rankType.value })
    const data = (res.data.results || res.data || []).slice(0, 15)
    const rankChart = charts.find((_, i) => i === 6) || initChart(rankRef.value)
    rankChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: data.map(i => i.title).reverse(), axisLabel: { width: 120, overflow: 'truncate' } },
      series: [{
        type: 'bar',
        data: data.map(i => rankType.value === 'orders' ? (i.order_count || 0)
                            : rankType.value === 'views' ? (i.view_count || 0)
                            : (i.score || i.order_count || 0)).reverse(),
        itemStyle: { color: '#409eff', borderRadius: [0, 4, 4, 0] }
      }],
      grid: { left: 140, right: 30, top: 10, bottom: 20 }
    }, true)
  } catch {}
}

const resizeAll = () => charts.forEach(c => c.resize())

onUnmounted(() => {
  window.removeEventListener('resize', resizeAll)
  charts.forEach(c => c.dispose())
})
</script>

<style scoped>
.statistics-page h2 { margin-bottom: 20px; }
</style>
