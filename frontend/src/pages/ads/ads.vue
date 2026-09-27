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
        <el-button v-if="userStore.hasPerm('ad:edit')" type="primary" :icon="Plus" @click="openCreate">
          新建广告位
        </el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column label="编码" min-width="140">
          <template #default="{ row }"><span class="mono">{{ row.code }}</span></template>
        </el-table-column>
        <el-table-column prop="image_count" label="图片数" width="90" />
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
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goImages(row)">图片管理</el-button>
            <el-button v-if="userStore.hasPerm('ad:edit')" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="userStore.hasPerm('ad:edit')" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pager">
        <el-pagination background layout="total, sizes, prev, pager, next" :total="total"
                       :current-page="query.page" :page-size="query.page_size"
                       :page-sizes="[20, 50, 100]" @current-change="load" @size-change="onSizeChange" />
      </div>
    </el-card>

    <el-drawer v-model="dialogVisible" :title="form.id ? '编辑广告位' : '新建广告位'" size="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="64" />
        </el-form-item>
        <el-form-item label="唯一编码" prop="code">
          <el-input v-model="form.code" :disabled="!!form.id" placeholder="如 home_banner（创建后不可改）" />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="form.start_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                          style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="form.end_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                          style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" />
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
const formRef = ref()
const form = reactive({
  id: null, name: '', code: '', start_time: null, end_time: null, status: 1, remark: '',
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
    const data = await api.adSlots(query)
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

function goImages(row) {
  uni.navigateTo({ url: `/pages/ads/images?slot=${row.id}&name=${encodeURIComponent(row.name)}` })
}

function openCreate() {
  Object.assign(form, { id: null, name: '', code: '', start_time: null, end_time: null, status: 1, remark: '' })
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id, name: row.name, code: row.code, start_time: row.start_time,
    end_time: row.end_time, status: row.status, remark: row.remark,
  })
  dialogVisible.value = true
}

async function submit() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (form.id) {
      await api.updateAdSlot(form.id, {
        name: form.name, start_time: form.start_time, end_time: form.end_time,
        status: form.status, remark: form.remark,
      })
      ElMessage.success('已保存')
    } else {
      await api.createAdSlot(form)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e) { /* 统一提示 */ } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除广告位「${row.name}」吗？其下图片记录将一并不可见。`, '删除广告位', { type: 'warning' })
  await api.deleteAdSlot(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(() => load(1))
</script>
