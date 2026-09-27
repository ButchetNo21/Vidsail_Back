<template>
  <el-container class="admin-shell">
    <el-aside width="220px" class="admin-aside">
      <div class="brand">
        <div class="brand-logo">
          <el-icon :size="22" color="#fff"><Promotion /></el-icon>
        </div>
        <div class="brand-text">
          <div class="brand-name">VidSail</div>
          <div class="brand-sub">运营管理后台</div>
        </div>
      </div>
      <el-menu class="admin-menu" :default-active="active" @select="onSelect">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-footer">V1.0.0</div>
    </el-aside>

    <el-container class="admin-body">
      <el-header class="admin-header" height="56px">
        <div class="page-title">{{ currentTitle }}</div>
        <el-dropdown @command="onCommand">
          <span class="user-chip">
            <el-avatar :size="28" class="user-avatar">{{ avatarText }}</el-avatar>
            <span class="user-name">{{ userStore.info?.username || '未登录' }}</span>
            <el-tag v-if="userStore.isSuper" size="small" type="primary" effect="light">超管</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="admin-main">
        <el-empty v-if="menus.length === 0" description="当前账号没有可用权限，请联系管理员" />
        <slot v-else />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user.js'
import { visibleMenus, MENUS } from '../menus.js'

const userStore = useUserStore()
const router = useRouter()

const pages = getCurrentPages()
const active = pages.length ? '/' + pages[pages.length - 1].route : ''
const menus = visibleMenus(userStore)
const currentTitle = computed(() => (MENUS.find((m) => m.path === active) || {}).title || '')
const avatarText = computed(() => (userStore.info?.username || 'V').slice(0, 1).toUpperCase())

onMounted(() => {
  if (!userStore.isLoggedIn) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }
  if (!userStore.info) {
    userStore.fetchMe().catch(() => {})
  }
})

function onSelect(path) {
  if (path === active) return
  uni.redirectTo({ url: path })
}

function onCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout().finally(() => uni.reLaunch({ url: '/pages/login/login' }))
  }
}
</script>

<style>
.admin-shell {
  height: 100vh;
  min-width: 1100px;
}
.admin-aside {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-right: 1px solid #ebeef5;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 18px;
}
.brand-logo {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #409eff, #79bbff);
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-name {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.brand-sub {
  font-size: 12px;
  color: #909399;
}
.admin-menu {
  flex: 1;
  border-right: none;
  padding: 6px 10px;
}
.admin-menu .el-menu-item {
  border-radius: 8px;
  margin-bottom: 4px;
  height: 44px;
}
.admin-menu .el-menu-item.is-active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}
.aside-footer {
  padding: 14px;
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid #ebeef5;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}
.user-avatar {
  background: #409eff;
  color: #fff;
  font-size: 14px;
}
.user-name {
  font-size: 14px;
  color: #303133;
}
.admin-main {
  padding: 18px;
  overflow-y: auto;
}
</style>
