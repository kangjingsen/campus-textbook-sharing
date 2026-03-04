import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getProfile } from '../api/modules'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user_info') || 'null'))
  const token = ref(localStorage.getItem('access_token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value && ['admin', 'superadmin'].includes(user.value.role))
  const username = computed(() => user.value?.username || '')

  async function login(credentials) {
    const res = await loginApi(credentials)
    token.value = res.data.access
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    await fetchProfile()
    return res
  }

  async function fetchProfile() {
    const res = await getProfile()
    user.value = res.data
    localStorage.setItem('user_info', JSON.stringify(res.data))
    return res.data
  }

  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  function updateUserInfo(info) {
    user.value = { ...user.value, ...info }
    localStorage.setItem('user_info', JSON.stringify(user.value))
  }

  return { user, token, isLoggedIn, isAdmin, username, login, fetchProfile, logout, updateUserInfo }
})
