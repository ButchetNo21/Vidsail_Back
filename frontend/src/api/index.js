import { request, uploadFile } from './request.js'

const GET = (url, params) => request({ url, data: params })
const POST = (url, data) => request({ url, method: 'POST', data })
const PATCH = (url, data) => request({ url, method: 'PATCH', data })
const PUT = (url, data) => request({ url, method: 'PUT', data })
const DEL = (url) => request({ url, method: 'DELETE' })

export const api = {
  // ---------- 认证 ----------
  login: (data) => POST('/api/auth/login', data),
  logout: (data) => POST('/api/auth/logout', data),
  me: () => GET('/api/auth/me'),
  permissions: () => GET('/api/auth/permissions'),

  // ---------- 账号管理（超管） ----------
  users: (params) => GET('/api/admin/users/', params),
  createUser: (data) => POST('/api/admin/users/', data),
  updateUser: (id, data) => PATCH(`/api/admin/users/${id}/`, data),
  deleteUser: (id) => DEL(`/api/admin/users/${id}/`),
  resetPassword: (id, data) => POST(`/api/admin/users/${id}/reset_password/`, data),

  // ---------- 仪表盘 ----------
  dashboardStats: () => GET('/api/admin/dashboard/stats'),

  // ---------- 卡密 ----------
  cards: (params) => GET('/api/admin/cards/', params),
  createCards: (data) => POST('/api/admin/cards/', data),
  updateCard: (id, data) => PATCH(`/api/admin/cards/${id}/`, data),
  cancelCard: (id) => POST(`/api/admin/cards/${id}/cancel/`),
  unbindCard: (id) => POST(`/api/admin/cards/${id}/unbind/`),
  cardLogs: (params) => GET('/api/admin/card-logs/', params),

  // ---------- 提示词 ----------
  prompts: (params) => GET('/api/admin/prompts/', params),
  createPrompt: (data) => POST('/api/admin/prompts/', data),
  updatePrompt: (id, data) => PATCH(`/api/admin/prompts/${id}/`, data),
  deletePrompt: (id) => DEL(`/api/admin/prompts/${id}/`),

  // ---------- 分类 / 标签 ----------
  categories: (params) => GET('/api/admin/categories/', params),
  createCategory: (data) => POST('/api/admin/categories/', data),
  updateCategory: (id, data) => PATCH(`/api/admin/categories/${id}/`, data),
  deleteCategory: (id) => DEL(`/api/admin/categories/${id}/`),
  tags: (params) => GET('/api/admin/tags/', params),
  createTag: (data) => POST('/api/admin/tags/', data),
  updateTag: (id, data) => PATCH(`/api/admin/tags/${id}/`, data),
  deleteTag: (id) => DEL(`/api/admin/tags/${id}/`),

  // ---------- 广告 ----------
  adSlots: (params) => GET('/api/admin/ad-slots/', params),
  createAdSlot: (data) => POST('/api/admin/ad-slots/', data),
  updateAdSlot: (id, data) => PATCH(`/api/admin/ad-slots/${id}/`, data),
  deleteAdSlot: (id) => DEL(`/api/admin/ad-slots/${id}/`),
  adImages: (params) => GET('/api/admin/ad-images/', params),
  createAdImage: (data) => POST('/api/admin/ad-images/', data),
  updateAdImage: (id, data) => PATCH(`/api/admin/ad-images/${id}/`, data),
  deleteAdImage: (id) => DEL(`/api/admin/ad-images/${id}/`),
  uploadAdImage: (id, file, position) => uploadFile(`/api/admin/ad-images/${id}/upload/`, file, { position }),
  removeAdImage: (id, position) => POST(`/api/admin/ad-images/${id}/remove_image/`, { position }),

  // ---------- 配置 ----------
  configs: (params) => GET('/api/admin/configs/', params),
  configDetail: (id) => GET(`/api/admin/configs/${id}/`),
  createConfig: (data) => POST('/api/admin/configs/', data),
  updateConfig: (id, data) => PATCH(`/api/admin/configs/${id}/`, data),
  deleteConfig: (id) => DEL(`/api/admin/configs/${id}/`),
}
