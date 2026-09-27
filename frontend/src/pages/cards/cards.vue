<template>
  <AdminShell>
    <el-card shadow="never" class="page-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="搜索卡密 / 设备号" clearable style="width: 220px"
                  @keyup.enter="load(1)" @clear="load(1)" />
        <el-select v-model="query.status" placeholder="状态" clearable style="width: 130px" @change="load(1)">
          <el-option v-for="(v, k) in CARD_STATUS" :key="k" :label="v.label" :value="Number(k)" />
        </el-select>
        <el-date-picker v-model="range" type="daterange" value-format="YYYY-MM-DD" range-separator="至"
                        start-placeholder="创建开始" end-placeholder="创建结束" style="width: 260px" @change="load(1)" />
        <el-button type="primary" :icon="Search" @click="load(1)">查询</el-button>
        <el-button :icon="RefreshLeft" @click="resetQuery">重置</el-button>
        <div class="spacer" />
        <el-button v-if="userStore.hasPerm('card:edit')" type="primary" :icon="Plus" @click="openCreate">
          生成卡密
        </el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column label="卡密" min-width="200">
          <template #default="{ row }">
            <span class="mono">{{ row.key }}</span>
            <el-button link type="primary" size="small" @click="copyKey(row.key)">复制</el-button>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="(CARD_STATUS[row.effective_status] || {}).type">
              {{ row.status_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="device_code" label="绑定设备" min-width="150">
          <template #default="{ row }">
            <span v-if="row.device_code" class="mono">{{ row.device_code }}</span>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="90" />
        <el-table-column prop="start_time" label="开始时间" width="165" />
        <el-table-column prop="end_time" label="结束时间" width="165" />
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="165" />
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button v-if="userStore.hasPerm('card:edit')" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="userStore.hasPerm('card:edit') && row.effective_status === 1" link type="warning"
                       @click="unbind(row)">解绑</el-button>
            <el-button v-if="userStore.hasPerm('card:cancel') && row.effective_status !== 3" link type="danger"
                       @click="cancel(row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pager">
        <el-pagination background layout="total, sizes, prev, pager, next" :total="total"
                       :current-page="query.page" :page-size="query.page_size"
                       :page-sizes="[20, 50, 100]" @current-change="load" @size-change="onSizeChange" />
      </div>
    </el-card>

    <!-- 生成卡密 -->
    <el-drawer v-model="createVisible" title="生成卡密" size="460px">
      <el-form ref="createFormRef" :model="createForm" :rules="rules" label-position="top">
        <el-form-item label="数量" prop="count">
          <el-input-number v-model="createForm.count" :min="1" :max="100" />
          <span class="muted" style="margin-left: 8px">一次最多 100 个</span>
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker v-model="createForm.start_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                          placeholder="默认立即生效" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker v-model="createForm.end_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                          placeholder="留空则永不过期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input-number v-model="createForm.amount" :min="0" :precision="2" :step="10" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="createForm.remark" type="textarea" :rows="2" maxlength="255" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="createVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitCreate">生成</el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 编辑卡密 -->
    <el-drawer v-model="editVisible" title="编辑卡密" size="460px">
      <el-form ref="editFormRef" :model="editForm" :rules="rules" label-position="top">
        <el-form-item label="卡密">
          <el-input :model-value="editForm.key" disabled class="mono" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker v-model="editForm.start_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                          style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker v-model="editForm.end_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                          style="width: 100%" />
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input-number v-model="editForm.amount" :min="0" :precision="2" :step="10" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="editForm.remark" type="textarea" :rows="2" maxlength="255" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="editVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button>
        </div>
      </template>
    </el-drawer>
  </AdminShell>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, RefreshLeft, Search } from '@element-plus/icons-vue'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api/index.js'
import { useUserStore } from '../../store/user.js'
import { CARD_STATUS } from '../../menus.js'

const userStore = useUserStore()
const items = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const range = ref(null)

const query = reactive({ keyword: '', status: null, page: 1, page_size: 20 })

const createVisible = ref(false)
const editVisible = ref(false)
const createFormRef = ref()
const editFormRef = ref()
const createForm = reactive({ count: 1, start_time: null, end_time: null, amount: 0, remark: '' })
const editForm = reactive({ id: null, key: '', start_time: null, end_time: null, amount: 0, remark: '' })

const rules = {
  end_time: [{
    validator: (rule, value, cb) => {
      if (createForm.start_time && value && value <= createForm.start_time) cb(new Error('结束时间需晚于开始时间'))
      else cb()
    },
    trigger: 'change',
  }],
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
    const data = await api.cards(params)
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
  query.status = null
  range.value = null
  load(1)
}

function copyKey(key) {
  uni.setClipboardData({ data: key, success: () => ElMessage.success('卡密已复制') })
}

function openCreate() {
  Object.assign(createForm, { count: 1, start_time: null, end_time: null, amount: 0, remark: '' })
  createVisible.value = true
}

async function submitCreate() {
  saving.value = true
  try {
    const created = await api.createCards(createForm)
    createVisible.value = false
    ElMessageBox.alert(
      created.map((c) => c.key).join('\n'),
      `已生成 ${created.length} 个卡密（点击复制第一个）`,
      {
        confirmButtonText: '复制并关闭',
        callback: () => {
          uni.setClipboardData({ data: created.map((c) => c.key).join('\n') })
        },
      })
    load(1)
  } catch (e) { /* 统一提示 */ } finally {
    saving.value = false
  }
}

function openEdit(row) {
  Object.assign(editForm, {
    id: row.id, key: row.key, start_time: row.start_time, end_time: row.end_time,
    amount: Number(row.amount), remark: row.remark,
  })
  editVisible.value = true
}

async function submitEdit() {
  saving.value = true
  try {
    await api.updateCard(editForm.id, {
      start_time: editForm.start_time, end_time: editForm.end_time,
      amount: editForm.amount, remark: editForm.remark,
    })
    editVisible.value = false
    ElMessage.success('已保存')
    load()
  } catch (e) { /* 统一提示 */ } finally {
    saving.value = false
  }
}

async function cancel(row) {
  await ElMessageBox.confirm(`确定取消卡密 ${row.key} 吗？取消后立即失效。`, '取消卡密', { type: 'warning' })
  await api.cancelCard(row.id)
  ElMessage.success('已取消')
  load()
}

async function unbind(row) {
  await ElMessageBox.confirm(`确定解绑设备 ${row.device_code} 吗？`, '解绑设备', { type: 'warning' })
  await api.unbindCard(row.id)
  ElMessage.success('已解绑')
  load()
}

onMounted(() => load(1))
</script>
