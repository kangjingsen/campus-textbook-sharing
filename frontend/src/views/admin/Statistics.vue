<template>
  <div class="statistics-page">
    <h2>统计分析</h2>

    <el-card style="margin-bottom: 16px;">
      <div class="section-filter">
        <span>统一筛选：</span>
        <el-select v-model="activeSection" placeholder="选择要看的统计图/数据" style="width: 280px;">
          <el-option label="全部模块" value="all" />
          <el-option label="流通率趋势" value="circulation" />
          <el-option label="价格与学院需求" value="price-college" />
          <el-option label="心愿单分类需求" value="wishlist" />
          <el-option label="取消率分析" value="cancellation" />
          <el-option label="需求与售卖排行" value="ranking" />
          <el-option label="优秀商家与价格指数" value="seller-price-index" />
          <el-option label="价格统计明细" value="price-table" />
          <el-option label="交易类型与活跃度" value="distribution" />
          <el-option label="热门教材排行" value="popular" />
        </el-select>
      </div>
    </el-card>

    <!-- 流通率趋势 -->
    <el-card v-show="shouldShow('circulation')" id="section-circulation" header="教材流通率月度趋势" style="margin-bottom: 20px;">
      <div ref="circulationRef" style="height: 350px;"></div>
    </el-card>

    <el-row v-show="shouldShow('price-college')" id="section-price-college" :gutter="16" style="margin-bottom: 20px;">
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

    <el-row v-show="shouldShow('wishlist')" id="section-cancellation" :gutter="16" style="margin-bottom: 20px;">
      <el-col :span="24">
        <el-card header="心愿单分类需求占比">
          <div ref="wishlistDemandRef" style="height: 320px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-show="shouldShow('cancellation')" id="section-ranking" :gutter="16" style="margin-bottom: 20px;">
      <el-col :span="8">
        <el-card header="取消率趋势">
          <div ref="cancelTrendRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="高取消分类">
          <div ref="cancelCategoryRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="高取消卖家">
          <div ref="cancelSellerRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-show="shouldShow('ranking')" :gutter="16" style="margin-bottom: 20px;">
      <el-col :span="12">
        <el-card header="售卖排行榜">
          <div ref="salesRankRef" style="height: 320px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="需求排行榜（心愿单+订单）">
          <div ref="demandRankRef" style="height: 320px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-show="shouldShow('seller-price-index')" :gutter="16" style="margin-bottom: 20px;">
      <el-col :span="12">
        <el-card header="优秀商家评分排行">
          <div ref="topSellerRef" style="height: 320px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="价格指数与环比">
          <div ref="priceMetricsRef" style="height: 320px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-show="shouldShow('price-table')" id="section-price-table" header="价格统计明细（均值/中位数/最小/最大/同比）" style="margin-bottom: 20px;">
      <el-table :data="priceMetricRows" size="small" stripe>
        <el-table-column prop="month" label="月份" width="110" />
        <el-table-column prop="avg_price" label="均价" width="90" />
        <el-table-column prop="median_price" label="中位数" width="90" />
        <el-table-column prop="min_price" label="最小值" width="90" />
        <el-table-column prop="max_price" label="最大值" width="90" />
        <el-table-column prop="price_index" label="价格指数" width="100" />
        <el-table-column prop="mom" label="环比(%)" width="100" />
        <el-table-column prop="yoy" label="同比(%)" width="100" />
      </el-table>
    </el-card>

    <el-row v-show="shouldShow('distribution')" id="section-distribution" :gutter="16" style="margin-bottom: 20px;">
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
    <el-card v-show="shouldShow('popular')" id="section-popular" header="热门教材排行">
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
  getUserActivity,
  getSalesRanking, getDemandRanking, getPriceMetrics, getWishlistDemand,
  getCancellationInsights, getTopSellersRating, getPopularTextbookDetail
} from '../../api/modules'


const circulationRef = ref(null)
const priceRef = ref(null)
const collegeRef = ref(null)
const txTypeRef = ref(null)
const categoryRef = ref(null)
const activityRef = ref(null)
const rankRef = ref(null)
const salesRankRef = ref(null)
const demandRankRef = ref(null)
const topSellerRef = ref(null)
const priceMetricsRef = ref(null)
const wishlistDemandRef = ref(null)
const cancelTrendRef = ref(null)
const cancelCategoryRef = ref(null)
const cancelSellerRef = ref(null)
const priceMetricRows = ref([])
const rankChartIns = ref(null)
const rankType = ref('views')
const activeSection = ref('all')
const charts = []

const shouldShow = (moduleName) => activeSection.value === 'all' || activeSection.value === moduleName

const initChart = (domRef) => {
  const chart = echarts.init(domRef)
  charts.push(chart)
  return chart
}

onMounted(async () => {
  try {
    const [cirRes, priceRes, collegeRes, txRes, catRes, actRes, salesRes, demandRes, topSellerRes, metricRes, wishDemandRes, cancelRes] = await Promise.all([
      getCirculationRate(), getPriceTrend(), getCollegeDemand(),
      getTransactionTypeDist(), getCategoryDistribution(), getUserActivity(),
      getSalesRanking({ limit: 12 }), getDemandRanking({ limit: 12 }),
      getTopSellersRating({ limit: 12 }), getPriceMetrics({ months: 24 }), getWishlistDemand(),
      getCancellationInsights({ months: 12, limit: 10 })
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
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          if (!params?.length) return ''
          const row = collegeData[params[0].dataIndex] || {}
          return [
            row.college || '',
            `总订单: ${row.order_count || 0}`,
            `取消订单: ${row.cancelled_count || 0}`,
            `教材订单: ${row.textbook_order_count || 0}`,
            `资料订单: ${row.resource_order_count || 0}`
          ].join('<br/>')
        }
      },
      xAxis: { type: 'category', data: collegeData.map(i => i.college), axisLabel: { rotate: 30 } },
      yAxis: { type: 'value' },
      legend: { data: ['总订单', '取消订单'] },
      series: [
        { name: '总订单', data: collegeData.map(i => i.order_count || 0), type: 'bar', itemStyle: { color: '#67c23a' } },
        { name: '取消订单', data: collegeData.map(i => i.cancelled_count || 0), type: 'bar', itemStyle: { color: '#f56c6c' } }
      ],
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
          { value: txData.free || 0, name: '赠送', itemStyle: { color: '#67c23a' } },
          { value: txData.cancelled_count || 0, name: '已取消', itemStyle: { color: '#f56c6c' } }
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

    // 售卖排行
    const salesChart = initChart(salesRankRef.value)
    const salesData = Array.isArray(salesRes.data) ? salesRes.data : []
    salesChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: salesData.map(i => i.seller_name).reverse() },
      series: [{
        type: 'bar',
        data: salesData.map(i => i.sales_amount || 0).reverse(),
        itemStyle: { color: '#409eff' }
      }],
      grid: { left: 90, right: 20, top: 20, bottom: 20 }
    })

    // 需求排行
    const demandChart = initChart(demandRankRef.value)
    const demandData = Array.isArray(demandRes.data) ? demandRes.data : []
    demandChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: demandData.map(i => i.title).reverse(), axisLabel: { width: 150, overflow: 'truncate' } },
      series: [{ type: 'bar', data: demandData.map(i => i.demand_score || 0).reverse(), itemStyle: { color: '#e6a23c' } }],
      grid: { left: 160, right: 20, top: 20, bottom: 20 }
    })

    // 优秀商家
    const topSellerChart = initChart(topSellerRef.value)
    const topSellerData = Array.isArray(topSellerRes.data) ? topSellerRes.data : []
    topSellerChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['平均评分', '完成率'] },
      xAxis: { type: 'category', data: topSellerData.map(i => i.seller_name), axisLabel: { rotate: 25 } },
      yAxis: [{ type: 'value', name: '评分' }, { type: 'value', name: '完成率(%)' }],
      series: [
        { name: '平均评分', type: 'bar', data: topSellerData.map(i => i.avg_rating || 0), itemStyle: { color: '#67c23a' } },
        { name: '完成率', type: 'line', yAxisIndex: 1, data: topSellerData.map(i => i.completion_rate || 0), itemStyle: { color: '#409eff' } }
      ],
      grid: { left: 50, right: 50, top: 30, bottom: 70 }
    })

    // 价格指数
    const priceMetricsChart = initChart(priceMetricsRef.value)
    const metricRows = metricRes.data?.metrics || []
    priceMetricRows.value = metricRows.slice().reverse()
    priceMetricsChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['价格指数', '环比(%)'] },
      xAxis: { type: 'category', data: metricRows.map(i => i.month) },
      yAxis: [{ type: 'value', name: '指数' }, { type: 'value', name: '环比(%)' }],
      series: [
        { name: '价格指数', type: 'line', smooth: true, data: metricRows.map(i => i.price_index || 0), itemStyle: { color: '#409eff' } },
        { name: '环比(%)', type: 'bar', yAxisIndex: 1, data: metricRows.map(i => i.mom ?? 0), itemStyle: { color: '#f56c6c' } }
      ],
      grid: { left: 55, right: 50, top: 30, bottom: 40 }
    })

    // 心愿单分类需求占比
    const wishChart = initChart(wishlistDemandRef.value)
    const wishData = wishDemandRes.data?.by_category || []
    wishChart.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['35%', '65%'],
        roseType: 'radius',
        data: wishData.map(i => ({ name: i.category, value: i.count }))
      }]
    })

    // 取消率趋势
    const cancelTrendChart = initChart(cancelTrendRef.value)
    const cancelTrendData = cancelRes.data?.trend || []
    cancelTrendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['取消率(%)', '取消订单'] },
      xAxis: { type: 'category', data: cancelTrendData.map(i => i.month) },
      yAxis: [{ type: 'value', name: '取消率(%)' }, { type: 'value', name: '取消数' }],
      series: [
        { name: '取消率(%)', type: 'line', smooth: true, data: cancelTrendData.map(i => i.cancel_rate || 0), itemStyle: { color: '#f56c6c' } },
        { name: '取消订单', type: 'bar', yAxisIndex: 1, data: cancelTrendData.map(i => i.cancelled_orders || 0), itemStyle: { color: '#e6a23c' } }
      ],
      grid: { left: 50, right: 50, top: 35, bottom: 35 }
    })

    // 高取消分类
    const cancelCategoryChart = initChart(cancelCategoryRef.value)
    const cancelCategoryData = cancelRes.data?.by_category || []
    cancelCategoryChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: cancelCategoryData.map(i => i.category).reverse(), axisLabel: { width: 120, overflow: 'truncate' } },
      series: [{ type: 'bar', data: cancelCategoryData.map(i => i.count || 0).reverse(), itemStyle: { color: '#f56c6c' } }],
      grid: { left: 130, right: 20, top: 20, bottom: 20 }
    })

    // 高取消卖家
    const cancelSellerChart = initChart(cancelSellerRef.value)
    const cancelSellerData = cancelRes.data?.by_seller || []
    cancelSellerChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: cancelSellerData.map(i => i.seller_name).reverse(), axisLabel: { width: 120, overflow: 'truncate' } },
      series: [{ type: 'bar', data: cancelSellerData.map(i => i.count || 0).reverse(), itemStyle: { color: '#909399' } }],
      grid: { left: 130, right: 20, top: 20, bottom: 20 }
    })

    window.addEventListener('resize', resizeAll)
  } catch (e) { console.error(e) }
})

const loadRank = async () => {
  try {
    const res = await getPopularTextbookDetail({ rank_type: rankType.value, limit: 15 })
    const data = (res.data?.data || []).slice(0, 15)
    if (!rankChartIns.value) {
      rankChartIns.value = initChart(rankRef.value)
    }
    rankChartIns.value.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          if (!params?.length) return ''
          const row = data[data.length - 1 - params[0].dataIndex] || {}
          if (rankType.value !== 'orders') {
            return `${row.title || ''}<br/>${params[0].seriesName || '数值'}: ${params[0].value || 0}`
          }
          return [
            row.title || '',
            `订单总数: ${row.order_count || 0}`,
            `完成订单: ${row.completed_order_count || 0}`,
            `取消订单: ${row.cancelled_order_count || 0}`
          ].join('<br/>')
        }
      },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: data.map(i => i.title).reverse(), axisLabel: { width: 120, overflow: 'truncate' } },
      series: [{
        name: rankType.value === 'orders' ? '订单数' : (rankType.value === 'views' ? '浏览量' : '综合热度'),
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
.section-filter { display: flex; align-items: center; gap: 10px; }
</style>
