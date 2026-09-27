// 后端 API 地址（按实际部署修改）
export const BASE_URL = 'http://127.0.0.1:8000'

// 拼接图片/媒体地址
export function mediaURL(path) {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  return BASE_URL + path
}
