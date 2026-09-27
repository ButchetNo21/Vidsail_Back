<template>
  <AdminShell>
    <el-card shadow="never" class="page-card">
      <div class="toolbar">
        <BackButton text="返回广告位" fallback="/pages/ads/ads" />
        <span class="section-title" style="margin: 0 0 0 8px">广告位：{{ slotName }}</span>
        <div class="spacer" />
        <el-input v-model="query.keyword" placeholder="名称 / 副标题" clearable style="width: 200px"
                  @keyup.enter="load(1)" @clear="load(1)" />
        <el-select v-model="query.is_valid" placeholder="有效性" clearable style="width: 120px" @change="load(1)">
          <el-option label="有效" :value="1" />
          <el-option label="无效" :value="0" />
        </el-select>
        <el-button v-if="userStore.hasPerm('ad:edit')" type="primary" :icon="Plus" @click="openCreate">
          新建图片
        </el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="name" label="名称" min-width="130" />
        <el-table-column prop="subtitle" label="副标题" min-width="130" show-overflow-tooltip />
        <el-table-column label="主图" width="90">
          <template #default="{ row }">
            <el-image v-if="row.image_url" :src="mediaURL(row.image_url)" :preview-src-list="[mediaURL(row.image_url)]"
                      preview-teleported fit="cover" style="width: 56px; height: 56px; border-radius: 6px" />
            <span v-else class="muted">未上传</span>
          </template>
        </el-table-column>
        <el-table-column label="副图" width="90">
          <template #default="{ row }">
            <el-image v-if="row.image2_url" :src="mediaURL(row.image2_url)"
                      :preview-src-list="[mediaURL(row.image2_url)]" preview-teleported fit="cover"
                      style="width: 56px; height: 56px; border-radius: 6px" />
            <span v-else class="muted">未上传</span>
          </template>
        </el-table-column>
        <el-table-column label="跳转链接" min-width="150">
          <template #default="{ row }">
            <span v-if="row.url" class="mono">{{ row.url }}</span>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="有效性" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_valid ? 'success' : 'info'">{{ row.is_valid ? '有效' : '无效' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="165" />
        <el-table-column prop="end_time" label="结束时间" width="165" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button v-if="userStore.hasPerm('ad:edit')" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="userStore.hasPerm('ad:edit')" link type="warning" @click="openUpload(row)">传图</el-button>
            <el-button v-if="userStore.hasPerm('ad:edit')" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pager">
        <el-pagination background layout="total, prev, pager, next" :total="total"
                       :current-page="query.page" :page-size="20" @current-change="load" />
      </div>
    </el-card>

    <!-- 新建/编辑图片信息 -->
    <el-drawer v-model="dialogVisible" :title="form.id ? '编辑图片' : '新建图片'" size="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="64" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="form.subtitle" maxlength="128" />
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="form.url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="是否有效">
          <el-switch v-model="form.is_valid" />
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

    <!-- 上传图片（最多两张） -->
    <el-drawer v-model="uploadVisible" title="上传图片（最多两张）" size="440px">
      <el-form label-width="90px">
        <el-form-item label="主图">
          <div class="upload-row">
            <el-image v-if="uploadRow.image_url" :src="mediaURL(uploadRow.image_url)" fit="cover"
                      style="width: 72px; height: 72px; border-radius: 8px" />
            <el-upload action="" :auto-upload="false" :show-file-list="false" accept="image/*"
                       :on-change="(f) => doUpload('image', f)">
              <el-button type="primary" plain :loading="uploading === 'image'">
                {{ uploadRow.image_url ? '替换主图' : '上传主图' }}
              </el-button>
            </el-upload>
            <el-button v-if="uploadRow.image_url" link type="danger" :loading="uploading === 'rm-image'"
                       @click="doRemove('image')">移除
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="副图">
          <div class="upload-row">
            <el-image v-if="uploadRow.image2_url" :src="mediaURL(uploadRow.image2_url)" fit="cover"
                      style="width: 72px; height: 72px; border-radius: 8px" />
            <el-upload action="" :auto-upload="false" :show-file-list="false" accept="image/*"
                       :on-change="(f) => doUpload('image2', f)">
              <el-button type="primary" plain :loading="uploading === 'image2'">
                {{ uploadRow.image2_url ? '替换副图' : '上传副图' }}
              </el-button>
            </el-upload>
            <el-button v-if="uploadRow.image2_url" link type="danger" :loading="uploading === 'rm-image2'"
                       @click="doRemove('image2')">移除
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <div class="muted">支持 jpg / png / webp，单张不超过 5MB；图片保存后立即生效。</div>
    </el-drawer>
  </AdminShell>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { onLoad } from '@dcloudio/uni-app'
import AdminShell from '../../components/AdminShell.vue'
import BackButton from '../../components/BackButton.vue'
import { api } from '../../api/index.js'
import { mediaURL } from '../../config.js'
import { useUserStore } from '../../store/user.js'

const userStore = useUserStore()
const slotId = ref('')
const slotName = ref('')
const items = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const query = reactive({ keyword: '', is_valid: null, page: 1 })

const dialogVisible = ref(false)
const uploadVisible = ref(false)
const formRef = ref()
const uploading = ref('')
const form = reactive({
  id: null, name: '', subtitle: '', url: '', is_valid: true, start_time: null, end_time: null, remark: '',
})
const uploadRow = reactive({ id: null, image_url: null, image2_url: null })

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  url: [{ type: 'url', message: '链接格式不正确（需以 http(s):// 开头）', trigger: 'blur' }],
}

onLoad((q) => {
  slotId.value = q.slot || ''
  slotName.value = decodeURIComponent(q.name || '')
  load(1)
})

async function load(page) {
  query.page = page || query.page
  loading.value = true
  try {
    const data = await api.adImages({ ...query, slot: slotId.value })
    items.value = data.items
    total.value = data.total
  } catch (e) { /* 统一提示 */ } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, {
    id: null, name: '', subtitle: '', url: '', is_valid: true, start_time: null, end_time: null, remark: '',
  })
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id, name: row.name, subtitle: row.subtitle, url: row.url, is_valid: row.is_valid,
    start_time: row.start_time, end_time: row.end_time, remark: row.remark,
  })
  dialogVisible.value = true
}

async function submit() {
  await formRef.value.validate()
  saving.value = true
  try {
    const data = {
      name: form.name, subtitle: form.subtitle, url: form.url, is_valid: form.is_valid,
      start_time: form.start_time, end_time: form.end_time, remark: form.remark,
    }
    if (form.id) {
      await api.updateAdImage(form.id, data)
      ElMessage.success('已保存')
    } else {
      await api.createAdImage({ ...data, slot: Number(slotId.value) })
      ElMessage.success('已创建，可点击「传图」上传图片')
    }
    dialogVisible.value = false
    load()
  } catch (e) { /* 统一提示 */ } finally {
    saving.value = false
  }
}

function openUpload(row) {
  Object.assign(uploadRow, { id: row.id, image_url: row.image_url, image2_url: row.image2_url })
  uploadVisible.value = true
}

async function doUpload(position, file) {
  if (!file || !file.raw) return
  uploading.value = position
  try {
    const data = await api.uploadAdImage(uploadRow.id, file.raw, position)
    Object.assign(uploadRow, { image_url: data.image_url, image2_url: data.image2_url })
    ElMessage.success('上传成功')
    load()
  } catch (e) { /* 统一提示 */ } finally {
    uploading.value = ''
  }
}

async function doRemove(position) {
  uploading.value = 'rm-' + position
  try {
    const data = await api.removeAdImage(uploadRow.id, position)
    Object.assign(uploadRow, { image_url: data.image_url, image2_url: data.image2_url })
    ElMessage.success('已移除')
    load()
  } catch (e) { /* 统一提示 */ } finally {
    uploading.value = ''
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除图片「${row.name}」吗？`, '删除图片', { type: 'warning' })
  await api.deleteAdImage(row.id)
  ElMessage.success('已删除')
  load()
}
</script>

<style>
.upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
