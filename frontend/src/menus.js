/** 后台菜单定义（AdminShell 与登录跳转共用） */
export const MENUS = [
  { path: '/pages/dashboard/dashboard', title: '首页', icon: 'Odometer', superOnly: true },
  { path: '/pages/cards/cards', title: '卡密管理', icon: 'Key', perm: 'card:view' },
  { path: '/pages/card-logs/card-logs', title: '卡密日志', icon: 'Document', perm: 'cardlog:view' },
  { path: '/pages/prompts/prompts', title: '提示词管理', icon: 'ChatDotRound', perm: 'prompt:view' },
  { path: '/pages/terms/terms', title: '分类与标签', icon: 'Collection', perm: 'category:view' },
  { path: '/pages/ads/ads', title: '广告位管理', icon: 'Picture', perm: 'ad:view' },
  { path: '/pages/configs/configs', title: '配置管理', icon: 'Setting', perm: 'config:view' },
  { path: '/pages/accounts/accounts', title: '账号管理', icon: 'User', superOnly: true },
]

export function visibleMenus(userStore) {
  return MENUS.filter((m) => (m.superOnly ? userStore.isSuper : !m.perm || userStore.hasPerm(m.perm)))
}

export function firstAllowedPath(userStore) {
  const menus = visibleMenus(userStore)
  return menus.length ? menus[0].path : '/pages/cards/cards'
}

export const CARD_STATUS = {
  0: { label: '未绑定', type: 'info' },
  1: { label: '已绑定', type: 'success' },
  2: { label: '已过期', type: 'warning' },
  3: { label: '已失效', type: 'danger' },
}

export const LOG_ACTIONS = {
  create: { label: '创建', type: 'primary' },
  update: { label: '修改', type: 'warning' },
  cancel: { label: '取消', type: 'danger' },
  bind: { label: '绑定', type: 'success' },
  unbind: { label: '解绑', type: 'info' },
}
