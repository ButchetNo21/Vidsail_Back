<template>
  <AdminShell>
    <el-card shadow="never" class="page-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="卡密 / 操作者" clearable style="width: 200px"
                  @keyup.enter="load(1)" @clear="load(1)" />
        <el-select v-model="query.action" placeholder="动作" clearable style="width: 120px" @change="load(1)">
          <el-option v-for="(v, k) in LOG_ACTIONS" :key="k" :label="v.label" :value="k" />
        </el-select>
        <el-select v-model="query.source" placeholder="来源" clearable style="width: 120px" @change="load(1)">
          <el-option label="后台" value="admin" />
          <el-option label="客户端" value="client" />
        </el-select>
        <el-date-picker v-model="range" type="daterange" value-format="YYYY-MM-DD" range-separator="至"
                        start-placeholder="开始日期" end-placeholder="结束日期" style="width: 260px" @change="load(1)" />
        <el-button type="primary" :icon="Search" @click="load(1)">查询</el-button>
        <el-button :icon="RefreshLeft" @click="resetQuery">重置</el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column label="卡密" min-width="180">
          <template #default="{ row }"><span class="mono">{{ row.card_key }}</span></template>
        </el-table-column>
        <el-table-column label="动作" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="(LOG_ACTIONS[row.action] || {}).type || 'info'">
              {{ (LOG_ACTIONS[row.action] || {}).label || row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.source === 'admin' ? 'primary' : 'warning'" effect="plain">
              {{ row.source === 'admin' ? '后台' : '客户端' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作者" width="180" />
        <el-table-column label="详情" min-width="220">
          <template #default="{ row }">
            <el-popover v-if="row.detail && JSON.stringify(row.detail) !== '{}'" placement="top" width="360"
                        trigger="hover">
              <template #reference>
                <el-button link type="primary">查看</el-button>
              </template>
              <pre class="pre-wrap muted" style="max-height: 260px; overflow: auto">{{ pretty(row.detail) }}</pre>
            </el-popover>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>

      <div class="table-pager">
        <el-pagination background layout="total, sizes, prev, pager, next" :total="total"
                       :current-page="query.page" :page-size="query.page_size"
                       :page-sizes="[20, 50, 100]" @current-change="load" @size-change="onSizeChange" />
      </div>
    </el-card>
  </AdminShell>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RefreshLeft, Search } from '@element-plus/icons-vue'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api/index.js'
import { LOG_ACTIONS } from '../../menus.js'

const items = ref([])
const total = ref(0)
const loading = ref(false)
const range = ref(null)
const query = reactive({ keyword: '', action: null, source: null, page: 1, page_size: 20 })

function pretty(detail) {
  try {
    return JSON.stringify(detail, null, 2)
  } catch (e) {
    return String(detail)
  }
}

async function load(page) {
  query.page = page || query.page
  loading.value = true
  try {
    const params = { ...query }
    if (range.value && range.value.length === 2) {
      params.created_from = range.value[0]
      params.created_to = range.value[1]
    }
    const data = await api.cardLogs(params)
    items.value = data.items
    total.value = data.total
  } catch (e) { /* 统一提示 */ } finally {
    loading.value = false
  }
}

function onSizeChange(size) {
  query.page_size = size
  load(1)
}

function resetQuery() {
  query.keyword = ''
  query.action = null
  query.source = null
  range.value = null
  load(1)
}

onMounted(() => load(1))
</script>
