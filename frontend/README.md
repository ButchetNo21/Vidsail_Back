# VidSail 前端管理后台（Vue3 + uniapp + Element Plus）

基于 uniapp（Vue3 + Vite）的管理后台，目标平台为 **H5**（桌面浏览器）。UI 使用 Element Plus
（白色主题 + 浅蓝色修饰，左侧菜单布局），图表使用 ECharts。

## 快速开始

```bash
cd frontend
npm install
npm run dev:h5        # 开发：http://localhost:5173
npm run build:h5      # 构建：dist/build/h5（静态文件，任意 Web 服务器可托管）
```

- 后端地址在 `src/config.js` 的 `BASE_URL` 修改（默认 `http://127.0.0.1:8000`）。
- 需要先启动后端（见 backend/README.md）。默认超级管理员：`admin / admin123`。

## 页面

| 路径 | 页面 | 权限 |
|---|---|---|
| /pages/login/login | 登录 | 公开 |
| /pages/dashboard/dashboard | 首页仪表盘（统计卡 + 趋势折线 + 状态饼图 + 最近日志） | 仅超管 |
| /pages/cards/cards | 卡密管理：生成(1-100批量)、编辑、取消、解绑、复制，按关键词/状态/日期搜索 | card:view/edit/cancel |
| /pages/card-logs/card-logs | 卡密日志：动作/来源/日期筛选，详情 JSON 查看 | cardlog:view |
| /pages/prompts/prompts | 提示词：多行内容、分类/标签最多3个、链接校验、软删除 | prompt:view/edit/delete |
| /pages/terms/terms | 分类与标签管理（两个 Tab） | category:view + edit |
| /pages/ads/ads | 广告位管理 | ad:view/edit |
| /pages/ads/images | 广告图片管理：上传/替换/移除（最多两张）、有效性、时间窗 | ad:view/edit |
| /pages/configs/configs | 配置管理：列表脱敏、详情明文 | config:view/edit |
| /pages/accounts/accounts | 账号管理：创建运营账号、权限勾选、重置密码、停用 | 仅超管 |

## 鉴权流程

- 登录后 access/refresh token 存 localStorage；所有请求自动带 `Authorization: Bearer`。
- 收到 401：自动用 refresh 换新 token 并重放原请求（并发单飞，只刷一次）；
  刷新失败则清空登录态并 `reLaunch` 到登录页，本次请求不执行。
- 菜单与按钮按权限码显隐（超管恒可见），后端同步做权限校验（前端仅是体验层）。

## 结构

```
src/
  api/request.js    uni.request 封装（JWT/401 续期/统一错误提示）+ XHR 上传
  api/index.js      全部后端接口
  store/user.js     pinia 用户状态（token、权限、hasPerm）
  menus.js          菜单定义 + 状态/日志动作映射
  components/AdminShell.vue   后台布局（侧边菜单 + 顶栏 + 内容区）
  pages/            各页面（pages.json 注册，navigationStyle custom）
```

## 注意

- Element Plus 与 ECharts 仅支持 H5 端；如需打包小程序/App 需替换组件库。
- 本地开发跨域由后端 `django-cors-headers` 放行（dev 配置允许全部来源）。
