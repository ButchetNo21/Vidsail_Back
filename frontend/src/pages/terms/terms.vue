<template>
  <AdminShell>
    <el-card shadow="never" class="page-card">
      <el-tabs v-model="tab">
        <el-tab-pane label="分类" name="category">
          <div class="toolbar">
            <el-input v-model="catQuery.keyword" placeholder="分类名称" clearable style="width: 200px"
                      @keyup.enter="loadCats(1)" @clear="loadCats(1)" />
            <el-button type="primary" :icon="Search" @click="loadCats(1)">查询</el-button>
            <div class="spacer" />
            <el-button v-if="userStore.hasPerm('category:edit')" type="primary" :icon="Plus"
                       @click="openCatDialog()">新建分类
            </el-button>
          </div>
          <el-table v-loading="catLoading" :data="cats" stripe>
            <el-table-column prop="name" label="名称" min-width="160" />
            <el-table-column prop="sort" label="排序" width="90" />
            <el-table-column prop="prompt_count" label="关联提示词" width="110" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'">
                  {{ row.status === 1 ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="165" />
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <el-button v-if="userStore.hasPerm('category:edit')" link type="primary"
                           @click="openCatDialog(row)">编辑
                </el-button>
                <el-button v-if="userStore.hasPerm('category:edit')" link type="danger" @click="removeCat(row)">删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-pager">
            <el-pagination background layout="total, prev, pager, next" :total="catTotal"
                           :current-page="catQuery.page" :page-size="20" @current-change="loadCats" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="标签" name="tag">
          <div class="toolbar">
            <el-input v-model="tagQuery.keyword" placeholder="标签名称" clearable style="width: 200px"
                      @keyup.enter="loadTags(1)" @clear="loadTags(1)" />
            <el-button type="primary" :icon="Search" @click="loadTags(1)">查询</el-button>
            <div class="spacer" />
            <el-button v-if="userStore.hasPerm('tag:edit')" type="primary" :icon="Plus" @click="openTagDialog()">
              新建标签
            </el-button>
          </div>
          <el-table v-loading="tagLoading" :data="tags" stripe>
            <el-table-column prop="name" label="名称" min-width="160" />
            <el-table-column prop="sort" label="排序" width="90" />
            <el-table-column prop="prompt_count" label="关联提示词" width="110" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'">
                  {{ row.status === 1 ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="165" />
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <el-button v-if="userStore.hasPerm('tag:edit')" link type="primary" @click="openTagDialog(row)">编辑
                </el-button>
                <el-button v-if="userStore.hasPerm('tag:edit')" link type="danger" @click="removeTag(row)">删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-pager">
            <el-pagination background layout="total, prev, pager, next" :total="tagTotal"
                           :current-page="tagQuery.page" :page-size="20" @current-change="loadTags" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-drawer v-model="catVisible" :title="catForm.id ? '编辑分类' : '新建分类'" size="400px">
      <el-form ref="catFormRef" :model="catForm" :rules="termRules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="catForm.name" maxlength="32" show-word-limit />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="catForm.sort" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="catForm.status" :active-value="1" :inactive-value="0" active-text="启用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="catVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitCat">保存</el-button>
        </div>
      </template>
    </el-drawer>

    <el-drawer v-model="tagVisible" :title="tagForm.id ? '编辑标签' : '新建标签'" size="400px">
      <el-form ref="tagFormRef" :model="tagForm" :rules="termRules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="tagForm.name" maxlength="32" show-word-limit />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="tagForm.sort" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="tagForm.status" :active-value="1" :inactive-value="0" active-text="启用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="tagVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitTag">保存</el-button>
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
import { useUserStore } from '../../store/user.js'

const userStore = useUserStore()
const tab = ref('category')
const saving = ref(false)

const cats = ref([])
const catTotal = ref(0)
const catLoading = ref(false)
const catQuery = reactive({ keyword: '', page: 1 })

const tags = ref([])
const tagTotal = ref(0)
const tagLoading = ref(false)
const tagQuery = reactive({ keyword: '', page: 1 })

const catVisible = ref(false)
const tagVisible = ref(false)
const catFormRef = ref()
const tagFormRef = ref()
const catForm = reactive({ id: null, name: '', sort: 0, status: 1 })
const tagForm = reactive({ id: null, name: '', sort: 0, status: 1 })

const termRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

async function loadCats(page) {
  catQuery.page = page || catQuery.page
  catLoading.value = true
  try {
    const data = await api.categories({ ...catQuery, page_size: 20 })
    cats.value = data.items
    catTotal.value = data.total
  } catch (e) { /* 统一提示 */ } finally {
    catLoading.value = false
  }
}

async function loadTags(page) {
  tagQuery.page = page || tagQuery.page
  tagLoading.value = true
  try {
    const data = await api.tags({ ...tagQuery, page_size: 20 })
    tags.value = data.items
    tagTotal.value = data.total
  } catch (e) { /* 统一提示 */ } finally {
    tagLoading.value = false
  }
}

function openCatDialog(row) {
  Object.assign(catForm, row ? { id: row.id, name: row.name, sort: row.sort, status: row.status }
    : { id: null, name: '', sort: 0, status: 1 })
  catVisible.value = true
}

function openTagDialog(row) {
  Object.assign(tagForm, row ? { id: row.id, name: row.name, sort: row.sort, status: row.status }
    : { id: null, name: '', sort: 0, status: 1 })
  tagVisible.value = true
}

async function submitCat() {
  await catFormRef.value.validate()
  saving.value = true
  try {
    if (catForm.id) await api.updateCategory(catForm.id, catForm)
    else await api.createCategory(catForm)
    catVisible.value = false
    ElMessage.success('已保存')
    loadCats()
  } catch (e) { /* 统一提示 */ } finally {
    saving.value = false
  }
}

async function submitTag() {
  await tagFormRef.value.validate()
  saving.value = true
  try {
    if (tagForm.id) await api.updateTag(tagForm.id, tagForm)
    else await api.createTag(tagForm)
    tagVisible.value = false
    ElMessage.success('已保存')
    loadTags()
  } catch (e) { /* 统一提示 */ } finally {
    saving.value = false
  }
}

async function removeCat(row) {
  await ElMessageBox.confirm(`确定删除分类「${row.name}」吗？`, '删除分类', { type: 'warning' })
  await api.deleteCategory(row.id)
  ElMessage.success('已删除')
  loadCats()
}

async function removeTag(row) {
  await ElMessageBox.confirm(`确定删除标签「${row.name}」吗？`, '删除标签', { type: 'warning' })
  await api.deleteTag(row.id)
  ElMessage.success('已删除')
  loadTags()
}

onMounted(() => {
  loadCats(1)
  loadTags(1)
})
</script>
