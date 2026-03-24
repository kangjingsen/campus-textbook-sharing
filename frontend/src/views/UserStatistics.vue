<template>
  <div class="user-statistics">
    <el-card>
      <div class="filter-row">
        <div class="title">我的统计分析</div>
        <div class="actions">
          <el-checkbox-group v-model="selectedPanels">
            <el-checkbox-button label="overview">概览</el-checkbox-button>
            <el-checkbox-button label="backlog">积压排行</el-checkbox-button>
            <el-checkbox-button label="demand">需求排行</el-checkbox-button>
            <el-checkbox-button label="popular">热门教材</el-checkbox-button>
            <el-checkbox-button label="sellers">优秀商家</el-checkbox-button>
          </el-checkbox-group>
          <el-input-number v-model="limit" :min="5" :max="30" />
          <el-button type="primary" @click="loadData">应用筛选</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" v-if="selectedPanels.includes('overview')" style="margin-top: 16px;">
      <el-col :span="6"><el-statistic title="我的教材" :value="overview.my_total_textbooks || 0" /></el-col>
      <el-col :span="6"><el-statistic title="在架教材" :value="overview.my_active_textbooks || 0" /></el-col>
      <el-col :span="6"><el-statistic title="积压数量" :value="overview.my_backlog_count || 0" /></el-col>
      <el-col :span="6"><el-statistic title="成交额" :value="overview.my_sales_amount || 0" prefix="¥" /></el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12" v-if="selectedPanels.includes('backlog')">
        <el-card header="积压排行榜（可考虑不卖/下架）">
          <el-table :data="backlogRows" size="small" stripe>
            <el-table-column type="index" width="50" />
            <el-table-column prop="title" label="教材" min-width="180" />
            <el-table-column prop="days_on_shelf" label="在架天数" width="90" />
            <el-table-column prop="view_count" label="浏览" width="70" />
            <el-table-column prop="backlog_score" label="积压分" width="90" />
            <el-table-column prop="suggestion" label="建议" min-width="120" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12" v-if="selectedPanels.includes('demand')">
        <el-card header="需求排行榜（全站）">
          <el-table :data="demandRows" size="small" stripe>
            <el-table-column type="index" width="50" />
            <el-table-column prop="title" label="教材" min-width="180" />
            <el-table-column prop="wishlist_count" label="心愿" width="80" />
            <el-table-column prop="order_count" label="订单" width="80" />
            <el-table-column prop="demand_score" label="需求分" width="90" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12" v-if="selectedPanels.includes('popular')">
        <el-card header="热门教材排行">
          <el-table :data="popularRows" size="small" stripe>
            <el-table-column type="index" width="50" />
            <el-table-column prop="title" label="教材" min-width="180" />
            <el-table-column prop="author" label="作者" min-width="120" />
            <el-table-column prop="view_count" label="浏览" width="80" />
            <el-table-column prop="order_count" label="订单" width="80" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12" v-if="selectedPanels.includes('sellers')">
        <el-card header="优秀商家评分排行">
          <el-table :data="sellerRows" size="small" stripe>
            <el-table-column type="index" width="50" />
            <el-table-column label="商家" min-width="140">
              <template #default="{ row }">
                <el-link type="primary" @click="goUserProfile(row.seller_id)">{{ row.seller_name }}</el-link>
              </template>
            </el-table-column>
            <el-table-column prop="avg_rating" label="评分" width="80" />
            <el-table-column prop="completion_rate" label="完成率(%)" width="110" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getUserInsights } from '../api/modules'

const selectedPanels = ref(['overview', 'backlog', 'demand', 'popular', 'sellers'])
const limit = ref(10)
const overview = ref({})
const backlogRows = ref([])
const demandRows = ref([])
const popularRows = ref([])
const sellerRows = ref([])
const router = useRouter()

const loadData = async () => {
  try {
    const res = await getUserInsights({ limit: limit.value })
    overview.value = res.data.overview || {}
    backlogRows.value = res.data.backlog_ranking || []
    demandRows.value = res.data.demand_ranking || []
    popularRows.value = res.data.popular_ranking || []
    sellerRows.value = res.data.top_sellers_rating || []
  } catch {
    console.warn('数据加载失败')
  }
}

const goUserProfile = (sellerId) => {
  if (!sellerId) return
  router.push(`/user/${sellerId}`)
}

onMounted(loadData)
</script>

<style scoped>
.filter-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.title { font-size: 18px; font-weight: 600; }
.actions { display: flex; align-items: center; gap: 10px; }
</style>
