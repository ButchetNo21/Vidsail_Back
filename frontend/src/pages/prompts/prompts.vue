<template>
  <AdminShell>
    <el-card shadow="never" class="page-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="名称 / 内容关键词" clearable style="width: 220px"
                  @keyup.enter="load(1)" @clear="load(1)" />
        <el-select v-model="query.category_id" placeholder="分类" clearable filterable style="width: 150px"
                   @change="load(1)">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-select v-model="query.tag_id" placeholder="标签" clearable filterable style="width: 140px" @change="load(1)">
          <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-select v-model="query.status" placeholder="状态" clearable style="width: 110px" @change="load(1)">
          <el-option label="启用" :value="1" />
          <el-option label="停用" :value="0" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="load(1)">查询</el-button>
        <el-button :icon="RefreshLeft" @click="resetQuery">重置</el-button>
        <div class="spacer" />
        <el-button v-if="userStore.hasPerm('prompt:edit')" type="primary" :icon="Plus" @click="openCreate">
          新建提示词
        </el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
        <el-table-column label="分类" min-width="140">
          <template #default="{ row }">
            <el-tag v-for="c in row.categories" :key="c.id" size="small" effect="plain" style="margin-right: 4px">
              {{ c.name }}
            </el-tag>
            <span v-if="!row.categories.length" class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="130">
          <template #default="{ row }">
            <el-tag v-for="t in row.tags" :key="t.id" size="small" type="success" effect="plain"
                    style="margin-right: 4px">
              {{ t.name }}
            </el-tag>
            <span v-if="!row.tags.length" class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="内容" min-width="220">
          <template #default="{ row }">
            <el-popover placement="top" width="420" trigger="hover">
              <template #reference>
                <span class="content-cell">{{ row.content }}</span>
              </template>
              <pre class="pre-wrap" style="max-height: 280px; overflow: auto; margin: 0">{{ row.content }}</pre>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_by_name" label="修改人" width="100" />
        <el-table-column prop="updated_at" label="修改时间" width="165" />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button v-if="userStore.hasPerm('prompt:edit')" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="userStore.hasPerm('prompt:delete')" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pager">
        <el-pagination background layout="total, sizes, prev, pager, next" :total="total"
                       :current-page="query.page" :page-size="query.page_size"
                       :page-sizes="[20, 50, 100]" @current-change="load" @size-change="onSizeChange" />
      </div>
    </el-card>

    <el-drawer v-model="dialogVisible" :title="form.id ? '编辑提示词' : '新建提示词'" size="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="64" show-word-limit />
        </el-form-item>
        <el-form-item label="分类" prop="category_ids">
          <el-select v-model="form.category_ids" multiple :multiple-limit="3" filterable placeholder="最多选3个"
                     style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签" prop="tag_ids">
          <el-select v-model="form.tag_ids" multiple :multiple-limit="3" filterable placeholder="最多选3个"
                     style="width: 100%">
            <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="9" maxlength="20000" show-word-limit
                    placeholder="支持多行文本" />
        </el-form-item>
        <el-form-item label="关联链接" prop="link">
          <el-input v-model="form.link" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" />
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
const categories = ref([])
const tags = ref([])
const query = reactive({ keyword: '', category_id: null, tag_id: null, status: null, page: 1, page_size: 20 })

const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  id: null, name: '', content: '', link: '', category_ids: [], tag_ids: [], status: 1,
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
  link: [{ type: 'url', message: '链接格式不正确（需以 http(s):// 开头）', trigger: 'blur' }],
}

async function load(page) {
  query.page = page || query.page
  loading.value = true
  try {
    const data = await api.prompts(query)
    items.value = data.items
    total.value = data.total
  } catch (e) { /* 统一提示 */ } finally {
    loading.value = false
  }
}

async function loadTerms() {
  try {
    const [c, t] = await Promise.all([api.categories({ page_size: 100 }), api.tags({ page_size: 100 })])
    categories.value = c.items
    tags.value = t.items
  } catch (e) { /* 统一提示 */ }
}

function onSizeChange(size) {
  query.page_size = size
  load(1)
}

function resetQuery() {
  query.keyword = ''
  query.category_id = null
  query.tag_id = null
  query.status = null
  load(1)
}

function openCreate() {
  Object.assign(form, { id: null, name: '', content: '', link: '', category_ids: [], tag_ids: [], status: 1 })
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id, name: row.name, content: row.content, link: row.link,
    category_ids: row.category_ids, tag_ids: row.tag_ids, status: row.status,
  })
  dialogVisible.value = true
}

async function submit() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payloadData = {
      name: form.name, content: form.content, link: form.link,
      category_ids: form.category_ids, tag_ids: form.tag_ids, status: form.status,
    }
    if (form.id) {
      await api.updatePrompt(form.id, payloadData)
      ElMessage.success('已保存')
    } else {
      await api.createPrompt(payloadData)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e) { /* 统一提示 */ } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除提示词「${row.name}」吗？删除后不可见（软删除）。`, '删除提示词', { type: 'warning' })
  await api.deletePrompt(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(() => {
  load(1)
  loadTerms()
})
</script>

<style>
.content-cell {
  display: inline-block;
  max-width: 100%;
  max-height: 44px;
  overflow: hidden;
  color: #606266;
  cursor: pointer;
}
</style>
