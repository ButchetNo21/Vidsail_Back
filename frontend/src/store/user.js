import { defineStore } from 'pinia'
import { api } from '../api/index.js'
import { clearAuth, getToken, setTokens } from '../api/request.js'

function storedUser() {
  try {
    return JSON.parse(uni.getStorageSync('vs_user') || 'null')
  } catch (e) {
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    info: storedUser(),
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isSuper: (s) => s.info?.role === 'super',
  },
  actions: {
    hasPerm(code) {
      return this.isSuper || (this.info?.permissions || []).includes(code)
    },
    async login(form) {
      const data = await api.login(form)
      setTokens(data.token, data.refresh)
      this.token = data.token
      this.info = data.user
      uni.setStorageSync('vs_user', JSON.stringify(data.user))
    },
    async fetchMe() {
      const data = await api.me()
      this.info = data
      uni.setStorageSync('vs_user', JSON.stringify(data))
    },
    async logout() {
      try {
        await api.logout({ refresh: uni.getStorageSync('vs_refresh') || '' })
      } catch (e) { /* 忽略登出接口错误 */ }
      clearAuth()
      this.token = ''
      this.info = null
    },
  },
})
