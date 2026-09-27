<template>
  <AdminShell>
    <el-card shadow="never" class="page-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="名称 / 编码" clearable style="width: 220px"
                  @keyup.enter="load(1)" @clear="load(1)" />
        <el-select v-model="query.status" placeholder="状态" clearable style="width: 120px" @change="load(1)">
          <el-option label="启用" :value="1" />
          <el-option label="停用" :value="0" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="load(1)">查询</el-button>
        <el-button :icon="RefreshLeft" @click="resetQuery">重置</el-button>
        <div class="spacer" />
        <el-button v-if="userStore.hasPerm('config:edit')" type="primary" :icon="Plus" @click="openCreate">
          新建配置
        </el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column label="编码" min-width="140">
          <template #default="{ row }"><span class="mono">{{ row.code }}</span></template>
        </el-table-column>
        <el-table-column label="内容" min-width="160">
          <template #default="{ row }">
            <span class="mono">{{ row.content }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="165" />
        <el-table-column prop="end_time" label="结束时间" width="165" />
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">查看</el-button>
            <el-button v-if="userStore.hasPerm('config:edit')" link type="primary" @click="openEdit(row)">编辑
            </el-button>
            <el-button v-if="userStore.hasPerm('config:edit')" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pager">
        <el-pagination background layout="total, sizes, prev, pager, next" :total="total"
                       :current-page="query.page" :page-size="query.page_size"
                       :page-sizes="[20, 50, 100]" @current-change="load" @size-change="onSizeChange" />
      </div>
    </el-card>

    <el-drawer v-model="dialogVisible" :title="form.id ? '编辑配置' : '新建配置'" size="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="64" />
        </el-form-item>
        <el-form-item label="唯一编码" prop="code">
          <el-input v-model="form.code" :disabled="!!form.id" placeholder="如 tts_ak_sk（创建后不可改）" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="5"
                    placeholder="如 ak/sk，可存 JSON 文本；列表页会脱敏显示" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="form.start_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                          style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="form.end_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                          style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
        </div>
      </template>
    </el-drawer>

    <el-drawer v-model="detailVisible" title="配置详情（脱敏内容仅此处可见）" size="520px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="名称">{{ detail.name }}</el-descriptions-item>
        <el-descriptions-item label="编码"><span class="mono">{{ detail.code }}</span></el-descriptions-item>
        <el-descriptions-item label="内容">
          <pre class="pre-wrap" style="margin: 0">{{ detail.content }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="备注">{{ detail.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
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

const userStore = useUserStore()
const items = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const query = reactive({ keyword: '', status: null, page: 1, page_size: 20 })

const dialogVisible = ref(false)
const detailVisible = ref(false)
const formRef = ref()
const detail = reactive({ name: '', code: '', content: '', remark: '' })
const form = reactive({
  id: null, name: '', code: '', content: '', status: 1, start_time: null, end_time: null, remark: '',
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  code: [{
    required: true,
    pattern: /^[A-Za-z0-9_-]{2,64}$/,
    message: '编码只能包含字母、数字、下划线、中划线',
    trigger: 'blur',
  }],
}

async function load(page) {
  query.page = page || query.page
  loading.value = true
  try {
    const data = await api.configs(query)
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
  load(1)
}

function openCreate() {
  Object.assign(form, {
    id: null, name: '', code: '', content: '', status: 1, start_time: null, end_time: null, remark: '',
  })
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id, name: row.name, code: row.code, content: '', status: row.status,
    start_time: row.start_time, end_time: row.end_time, remark: row.remark,
  })
  dialogVisible.value = true
  // 列表内容是脱敏的，编辑前拉取明文
  api.configDetail(row.id).then((data) => {
    form.content = data.content
  }).catch(() => {})
}

async function viewDetail(row) {
  const data = await api.configDetail(row.id)
  Object.assign(detail, data)
  detailVisible.value = true
}

async function submit() {
  await formRef.value.validate()
  saving.value = true
  try {
    const data = {
      name: form.name, content: form.content, status: form.status,
      start_time: form.start_time, end_time: form.end_time, remark: form.remark,
    }
    if (form.id) {
      await api.updateConfig(form.id, { ...data, code: form.code })
      ElMessage.success('已保存')
    } else {
      await api.createConfig({ ...data, code: form.code })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e) { /* 统一提示 */ } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除配置「${row.name}」吗？`, '删除配置', { type: 'warning' })
  await api.deleteConfig(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(() => load(1))
</script>
