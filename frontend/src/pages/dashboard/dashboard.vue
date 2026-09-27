<template>
  <AdminShell>
    <view v-if="userStore.isSuper">
      <el-row :gutter="16">
        <el-col v-for="card in statCards" :key="card.label" :span="6">
          <el-card shadow="never" class="page-card stat-card">
            <div class="stat-top">
              <span class="stat-label">{{ card.label }}</span>
              <el-icon :size="20" :color="card.color"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="14">
          <el-card shadow="never" class="page-card">
            <template #header><span class="section-title">近 7 天卡密趋势</span></template>
            <div ref="trendRef" class="chart chart-lg chart-trend" />
          </el-card>
        </el-col>
        <el-col :span="10">
          <el-card shadow="never" class="page-card">
            <template #header><span class="section-title">卡密状态分布</span></template>
            <div ref="pieRef" class="chart chart-lg chart-pie" />
          </el-card>
        </el-col>
      </el-row>

      <el-row style="margin-top: 16px">
        <el-col :span="24">
          <el-card shadow="never" class="page-card">
            <template #header><span class="section-title">最近卡密日志</span></template>
            <el-table :data="recentLogs" stripe size="default">
              <el-table-column prop="card_key" label="卡密" min-width="180">
                <template #default="{ row }"><span class="mono">{{ row.card_key }}</span></template>
              </el-table-column>
              <el-table-column label="动作" width="90">
                <template #default="{ row }">
                  <el-tag size="small" :type="(LOG_ACTIONS[row.action] || {}).type || 'info'">
                    {{ (LOG_ACTIONS[row.action] || {}).label || row.action }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="operator_name" label="操作者" width="160" />
              <el-table-column prop="created_at" label="时间" width="180" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </view>
  </AdminShell>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api/index.js'
import { useUserStore } from '../../store/user.js'
import { CARD_STATUS, LOG_ACTIONS } from '../../menus.js'

const userStore = useUserStore()
const stats = ref(null)
const recentLogs = ref([])
const trendRef = ref()
const pieRef = ref()
let trendChart = null
let pieChart = null

const statCards = computed(() => {
  const c = stats.value?.cards || {}
  const n = stats.value?.counts || {}
  return [
    { label: '卡密总数', value: c.total ?? '-', color: '#409eff', icon: 'Key' },
    { label: '未绑定', value: c.unbound ?? '-', color: '#909399', icon: 'CircleClose' },
    { label: '已绑定', value: c.bound ?? '-', color: '#67c23a', icon: 'CircleCheck' },
    { label: '已过期', value: c.expired ?? '-', color: '#e6a23c', icon: 'Timer' },
    { label: '已失效', value: c.invalid ?? '-', color: '#f56c6c', icon: 'CircleCloseFilled' },
    { label: '今日新增', value: c.today_new ?? '-', color: '#409eff', icon: 'Plus' },
    { label: '设备数', value: n.devices ?? '-', color: '#409eff', icon: 'Monitor' },
    { label: '提示词数', value: n.prompts ?? '-', color: '#409eff', icon: 'ChatDotRound' },
  ]
})

function elOf(refVal) {
  return refVal && (refVal.$el || refVal)
}

function renderCharts() {
  const trend = stats.value?.trend || { days: [], card_created: [], card_bound: [] }
  if (trendChart) {
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['生成', '绑定'], top: 0 },
      grid: { left: 40, right: 20, top: 36, bottom: 28 },
      xAxis: { type: 'category', data: trend.days },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        { name: '生成', type: 'line', smooth: true, data: trend.card_created, itemStyle: { color: '#409eff' }, areaStyle: { color: 'rgba(64,158,255,0.12)' } },
        { name: '绑定', type: 'line', smooth: true, data: trend.card_bound, itemStyle: { color: '#67c23a' } },
      ],
    })
  }
  const c = stats.value?.cards || {}
  if (pieChart) {
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: ['40%', '66%'],
        center: ['50%', '44%'],
        label: { formatter: '{b}: {c}' },
        data: [
          { name: CARD_STATUS[0].label, value: c.unbound || 0, itemStyle: { color: '#909399' } },
          { name: CARD_STATUS[1].label, value: c.bound || 0, itemStyle: { color: '#67c23a' } },
          { name: CARD_STATUS[2].label, value: c.expired || 0, itemStyle: { color: '#e6a23c' } },
          { name: CARD_STATUS[3].label, value: c.invalid || 0, itemStyle: { color: '#f56c6c' } },
        ],
      }],
    })
  }
}

function onResize() {
  trendChart && trendChart.resize()
  pieChart && pieChart.resize()
}

onMounted(async () => {
  if (!userStore.isSuper) return
  try {
    stats.value = await api.dashboardStats()
    recentLogs.value = stats.value.recent_logs || []
    await nextTick()
    // uni-app 编译后模板 ref 不可靠，H5 下直接按 class 查询容器
    const tEl = document.querySelector('.chart-trend')
    const pEl = document.querySelector('.chart-pie')
    if (tEl) {
      trendChart = echarts.init(tEl)
      pieChart = pEl ? echarts.init(pEl) : null
      renderCharts()
      window.addEventListener('resize', onResize)
    }
  } catch (e) { /* 统一错误提示 */ }
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  trendChart && trendChart.dispose()
  pieChart && pieChart.dispose()
})
</script>

<style>
.stat-card .stat-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stat-label {
  color: #909399;
  font-size: 13px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-top: 8px;
}
.chart {
  width: 100%;
}
.chart-lg {
  height: 300px;
}
</style>
