import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const wishlistUpdateTime = ref(0)

  function notifyWishlistUpdate() {
    wishlistUpdateTime.value = Date.now()
  }

  return { wishlistUpdateTime, notifyWishlistUpdate }
})
