<template>
  <AdminShell>
    <el-card shadow="never" class="page-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="用户名 / 姓名" clearable style="width: 220px"
                  @keyup.enter="load(1)" @clear="load(1)" />
        <el-button type="primary" :icon="Search" @click="load(1)">查询</el-button>
        <div class="spacer" />
        <el-button type="primary" :icon="Plus" @click="openCreate">新建运营账号</el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="username" label="用户名" min-width="130" />
        <el-table-column prop="real_name" label="姓名" min-width="110">
          <template #default="{ row }">{{ row.real_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限" min-width="260">
          <template #default="{ row }">
            <el-tag v-for="p in row.permissions" :key="p" size="small" effect="plain" style="margin: 0 4px 4px 0">
              {{ permLabel(p) }}
            </el-tag>
            <span v-if="!(row.permissions || []).length" class="muted">无权限</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="165">
          <template #default="{ row }">{{ row.last_login_at || '从未登录' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="165" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="resetPwd(row)">重置密码</el-button>
            <el-button link type="danger" @click="remove(row)">{{ row.is_active ? '停用' : '已停用' }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pager">
        <el-pagination background layout="total, sizes, prev, pager, next" :total="total"
                       :current-page="query.page" :page-size="query.page_size"
                       :page-sizes="[20, 50, 100]" @current-change="load" @size-change="onSizeChange" />
      </div>
    </el-card>

    <el-drawer v-model="dialogVisible" :title="form.id ? '编辑运营账号' : '新建运营账号'" size="580px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!form.id" placeholder="字母/数字/下划线，3-32位" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.real_name" maxlength="32" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password
                    :placeholder="form.id ? '留空则不修改密码' : '至少6位'" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="权限勾选">
          <div class="perm-groups">
            <div v-for="group in permGroups" :key="group.group" class="perm-group">
              <div class="perm-group-title">{{ group.group }}</div>
              <el-checkbox-group v-model="form.permissions">
                <el-checkbox v-for="item in group.items" :key="item.code" :value="item.code">
                  {{ item.label }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
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
import { Plus, Search } from '@element-plus/icons-vue'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api/index.js'
import { PERMISSION_LABELS } from './labels.js'

const items = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const permGroups = ref([])
const query = reactive({ keyword: '', page: 1, page_size: 20 })

const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  id: null, username: '', real_name: '', password: '', is_active: true, permissions: [],
})

const rules = {
  username: [{
    required: true, pattern: /^[A-Za-z0-9_]{3,32}$/,
    message: '字母/数字/下划线，3-32位', trigger: 'blur',
  }],
  password: [{
    validator: (rule, value, cb) => {
      if (!form.id && (!value || value.length < 6)) cb(new Error('请输入至少6位密码'))
      else if (value && value.length < 6) cb(new Error('密码至少6位'))
      else cb()
    },
    trigger: 'blur',
  }],
}

function permLabel(code) {
  return PERMISSION_LABELS[code] || code
}

async function load(page) {
  query.page = page || query.page
  loading.value = true
  try {
    const data = await api.users(query)
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

function openCreate() {
  Object.assign(form, { id: null, username: '', real_name: '', password: '', is_active: true, permissions: [] })
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id, username: row.username, real_name: row.real_name, password: '',
    is_active: row.is_active, permissions: [...(row.permissions || [])],
  })
  dialogVisible.value = true
}

async function submit() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (form.id) {
      const data = { real_name: form.real_name, is_active: form.is_active, permissions: form.permissions }
      if (form.password) data.password = form.password
      await api.updateUser(form.id, data)
      ElMessage.success('已保存')
    } else {
      await api.createUser({
        username: form.username, real_name: form.real_name, password: form.password,
        is_active: form.is_active, permissions: form.permissions,
      })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e) { /* 统一提示 */ } finally {
    saving.value = false
  }
}

async function resetPwd(row) {
  const { value } = await ElMessageBox.prompt(`为账号 ${row.username} 设置新密码（至少6位）`, '重置密码', {
    inputType: 'password', inputPattern: /^.{6,}$/, inputErrorMessage: '密码至少6位',
  })
  await api.resetPassword(row.id, { password: value })
  ElMessage.success('密码已重置')
}

async function remove(row) {
  if (!row.is_active) return
  await ElMessageBox.confirm(`确定停用账号 ${row.username} 吗？停用后无法登录。`, '停用账号', { type: 'warning' })
  await api.deleteUser(row.id)
  ElMessage.success('已停用')
  load()
}

onMounted(async () => {
  load(1)
  try {
    permGroups.value = await api.permissions()
  } catch (e) { /* 统一提示 */ }
})
</script>

<style>
.perm-groups {
  width: 100%;
  max-height: 260px;
  overflow: auto;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 10px 14px;
}
.perm-group-title {
  font-weight: 600;
  font-size: 13px;
  color: #303133;
  margin: 8px 0 2px;
}
</style>
