import { ElMessage } from 'element-plus'
import { BASE_URL } from '../config.js'

const TOKEN_KEY = 'vs_token'
const REFRESH_KEY = 'vs_refresh'
const USER_KEY = 'vs_user'

export function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

export function setTokens(token, refresh) {
  uni.setStorageSync(TOKEN_KEY, token)
  uni.setStorageSync(REFRESH_KEY, refresh || '')
}

export function clearAuth() {
  uni.removeStorageSync(TOKEN_KEY)
  uni.removeStorageSync(REFRESH_KEY)
  uni.removeStorageSync(USER_KEY)
}

export function gotoLogin() {
  clearAuth()
  uni.reLaunch({ url: '/pages/login/login' })
}

// 单飞刷新：并发 401 时只发一次 refresh 请求
let refreshingPromise = null

function doRefresh() {
  if (refreshingPromise) return refreshingPromise
  refreshingPromise = new Promise((resolve) => {
    uni.request({
      url: BASE_URL + '/api/auth/refresh',
      method: 'POST',
      data: { refresh: uni.getStorageSync(REFRESH_KEY) || '' },
      success: (res) => {
        const body = res.data || {}
        if (res.statusCode === 200 && body.code === 0 && body.data && body.data.access) {
          setTokens(body.data.access, body.data.refresh || '')
          resolve(true)
        } else {
          resolve(false)
        }
      },
      fail: () => resolve(false)
    })
  }).finally(() => {
    refreshingPromise = null
  })
  return refreshingPromise
}

/**
 * 统一请求封装：
 * - 自动携带 JWT；
 * - 401 时尝试用 refresh token 续期并重放一次，失败则清空登录态并跳转登录页；
 * - 业务失败统一弹出 message，成功返回 data 字段。
 */
export function request({ url, method = 'GET', data = {}, header = {} }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: { Authorization: getToken() ? 'Bearer ' + getToken() : '', ...header },
      success: async (res) => {
        const status = res.statusCode
        const body = res.data || {}
        if (status === 401 || body.code === 401) {
          const ok = await doRefresh()
          if (ok) {
            try {
              resolve(await request({ url, method, data, header }))
            } catch (e) {
              reject(e)
            }
          } else {
            ElMessage.error('登录已过期，请重新登录')
            gotoLogin()
            reject(new Error('unauthorized'))
          }
          return
        }
        if (status >= 400 || (typeof body.code === 'number' && body.code !== 0)) {
          ElMessage.error(body.message || `请求失败（${status}）`)
          reject(body)
          return
        }
        resolve(body.data !== undefined ? body.data : body)
      },
      fail: (err) => {
        ElMessage.error('网络异常，请确认后端服务已启动')
        reject(err)
      }
    })
  })
}

/** H5 文件上传（multipart），返回 data 字段。 */
export function uploadFile(url, file, formData = {}) {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    Object.keys(formData).forEach((k) => form.append(k, formData[k]))
    form.append('file', file)
    const xhr = new XMLHttpRequest()
    xhr.open('POST', BASE_URL + url)
    xhr.setRequestHeader('Authorization', 'Bearer ' + getToken())
    xhr.onload = () => {
      let body = {}
      try {
        body = JSON.parse(xhr.responseText)
      } catch (e) { /* ignore */ }
      if (xhr.status === 401 || body.code === 401) {
        ElMessage.error('登录已过期，请重新登录')
        gotoLogin()
        reject(body)
        return
      }
      if (xhr.status >= 400 || body.code !== 0) {
        ElMessage.error(body.message || '上传失败')
        reject(body)
        return
      }
      resolve(body.data)
    }
    xhr.onerror = () => {
      ElMessage.error('网络异常，上传失败')
      reject(new Error('network'))
    }
    xhr.send(form)
  })
}
