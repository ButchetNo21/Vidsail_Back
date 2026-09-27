<template>
  <view class="login-wrap">
    <view class="login-card">
      <view class="login-brand">
        <view class="login-logo"><el-icon :size="26" color="#fff"><Promotion /></el-icon></view>
        <view class="login-title">VidSail 管理后台</view>
        <view class="login-sub">卡密 · 提示词 · 广告 · 配置 一站式运营</view>
      </view>
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="submit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password
                    @keyup.enter="submit" />
        </el-form-item>
        <el-button class="login-btn" type="primary" size="large" :loading="loading" @click="submit">
          登 录
        </el-button>
      </el-form>
      <view class="login-tip">超级管理员 / 运营账号均在此登录，鉴权过期将自动跳回本页</view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '../../store/user.js'
import { firstAllowedPath } from '../../menus.js'

const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

onMounted(() => {
  if (userStore.isLoggedIn && userStore.info) {
    uni.reLaunch({ url: firstAllowedPath(userStore) })
  }
})

async function submit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    uni.reLaunch({ url: firstAllowedPath(userStore) })
  } catch (e) {
    /* 错误提示由 request 统一弹出 */
  } finally {
    loading.value = false
  }
}
</script>

<style>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #d9ecff 0%, #eef6ff 45%, #f5f7fa 100%);
}
.login-card {
  width: 400px;
  background: #fff;
  border-radius: 14px;
  padding: 40px 36px 28px;
  box-shadow: 0 10px 40px rgba(64, 158, 255, 0.15);
}
.login-brand {
  text-align: center;
  margin-bottom: 26px;
}
.login-logo {
  width: 52px;
  height: 52px;
  margin: 0 auto 12px;
  border-radius: 14px;
  background: linear-gradient(135deg, #409eff, #79bbff);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}
.login-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}
.login-btn {
  width: 100%;
  margin-top: 6px;
  letter-spacing: 4px;
}
.login-tip {
  margin-top: 18px;
  text-align: center;
  font-size: 12px;
  color: #c0c4cc;
}
</style>
