import api from './index'

// 用户认证
export const login = (data) => api.post('/users/login/', data)
export const register = (data) => api.post('/users/register/', data)
export const refreshToken = (data) => api.post('/users/token/refresh/', data)
export const forgotPassword = (data) => api.post('/users/forgot-password/', data)
export const resetPassword = (data) => api.post('/users/reset-password/', data)
export const getProfile = () => api.get('/users/profile/')
export const updateProfile = (data) => {
  const formData = new FormData()
  for (const key in data) {
    if (data[key] !== null && data[key] !== undefined) {
      formData.append(key, data[key])
    }
  }
  return api.patch('/users/profile/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
export const changePassword = (data) => api.post('/users/change-password/', data)
export const getUserDetail = (id) => api.get(`/users/${id}/`)
export const getAdminUserList = (params) => api.get('/users/admin/list/', { params })
export const updateAdminUser = (id, data) => api.patch(`/users/admin/${id}/`, data)

// 教材
export const getTextbooks = (params) => api.get('/textbooks/', { params })
export const searchTextbooks = (params) => api.get('/textbooks/search/', { params })
export const getTextbookDetail = (id) => api.get(`/textbooks/${id}/`)
export const createTextbook = (data) => {
  const formData = new FormData()
  for (const key in data) {
    if (data[key] !== null && data[key] !== undefined) {
      formData.append(key, data[key])
    }
  }
  return api.post('/textbooks/create/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
export const updateTextbook = (id, data) => api.patch(`/textbooks/${id}/edit/`, data)
export const deleteTextbook = (id) => api.delete(`/textbooks/${id}/delete/`)
export const getMyTextbooks = (params) => api.get('/textbooks/my/', { params })
export const exportMyTextbooks = (params) => api.get('/textbooks/my/', {
  params: { ...(params || {}), export: 1 },
  responseType: 'blob'
})
export const importMyTextbooks = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/textbooks/my/import/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
export const adminDeleteTextbook = (id) => api.delete(`/textbooks/admin/${id}/delete/`)

// 点赞/点踩
export const getTextbookVotes = (id) => api.get(`/textbooks/${id}/vote/`)
export const voteTextbook = (id, vote) => api.post(`/textbooks/${id}/vote/`, { vote })

// 评论
export const getTextbookComments = (id, params) => api.get(`/textbooks/${id}/comments/`, { params })
export const createComment = (id, data) => api.post(`/textbooks/${id}/comments/`, data)
export const deleteComment = (id) => api.delete(`/textbooks/comments/${id}/delete/`)

// 在线资料共享
export const getResources = (params) => api.get('/textbooks/resources/', { params })
export const uploadResource = (data) => {
  const formData = new FormData()
  for (const key in data) {
    if (data[key] !== null && data[key] !== undefined) {
      formData.append(key, data[key])
    }
  }
  return api.post('/textbooks/resources/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
export const getResourceDetail = (id) => api.get(`/textbooks/resources/${id}/`)
export const deleteResource = (id) => api.delete(`/textbooks/resources/${id}/`)
export const downloadResource = (id) => api.post(`/textbooks/resources/${id}/download/`)
export const createResourceOrder = (data) => api.post('/textbooks/resources/orders/create/', data)
export const getResourceOrders = (params) => api.get('/textbooks/resources/orders/', { params })
export const getResourceOrderDetail = (id) => api.get(`/textbooks/resources/orders/${id}/`)
export const confirmResourceOrder = (id, data) => {
  const isFormData = typeof FormData !== 'undefined' && data instanceof FormData
  return api.post(`/textbooks/resources/orders/${id}/confirm/`, data, isFormData
    ? { headers: { 'Content-Type': 'multipart/form-data' } }
    : undefined)
}
export const completeResourceOrder = (id, data) => api.post(`/textbooks/resources/orders/${id}/complete/`, data)
export const sellerCompleteResourceOrder = (id) => api.post(`/textbooks/resources/orders/${id}/seller-complete/`)
export const cancelResourceOrder = (id) => api.post(`/textbooks/resources/orders/${id}/cancel/`)

// 分类
export const getCategoryTree = () => api.get('/textbooks/categories/tree/')
export const getCategoryFlat = () => api.get('/textbooks/categories/flat/')
export const manageCategories = () => api.get('/textbooks/categories/manage/')
export const createCategory = (data) => api.post('/textbooks/categories/manage/', data)
export const updateCategory = (id, data) => api.patch(`/textbooks/categories/manage/${id}/`, data)
export const deleteCategory = (id) => api.delete(`/textbooks/categories/manage/${id}/`)

// 订单
export const createOrder = (data) => api.post('/orders/create/', data)
export const getOrders = (params) => api.get('/orders/', { params })
export const getOrderDetail = (id) => api.get(`/orders/${id}/`)
export const confirmOrder = (id) => api.post(`/orders/${id}/confirm/`)
export const completeOrder = (id) => api.post(`/orders/${id}/complete/`)
export const cancelOrder = (id) => api.post(`/orders/${id}/cancel/`)
export const returnOrder = (id) => api.post(`/orders/${id}/return/`)

// 消息
export const getConversations = () => api.get('/messages/conversations/')
export const createConversation = (data) => api.post('/messages/conversations/create/', data)
export const getMessages = (conversationId, params) =>
  api.get(`/messages/conversations/${conversationId}/messages/`, { params })
export const sendMessage = (conversationId, data) =>
  api.post(`/messages/conversations/${conversationId}/send/`, data)
export const getUnreadCount = () => api.get('/messages/unread/')

// 审核
export const getPendingReviews = (params) => api.get('/reviews/pending/', { params })
export const reviewAction = (id, data) => api.post(`/reviews/action/${id}/`, data)
export const getReviewRecords = (params) => api.get('/reviews/records/', { params })
export const getSensitiveWords = (params) => api.get('/reviews/sensitive-words/', { params })
export const createSensitiveWord = (data) => api.post('/reviews/sensitive-words/', data)
export const updateSensitiveWord = (id, data) => api.patch(`/reviews/sensitive-words/${id}/`, data)
export const deleteSensitiveWord = (id) => api.delete(`/reviews/sensitive-words/${id}/`)

// 推荐
export const getRecommendations = (params) => api.get('/recommendations/', { params })
export const getPopularTextbooks = () => api.get('/recommendations/popular/')
export const getBrowsingHistory = (params) => api.get('/recommendations/history/', { params })
export const getWishlist = (params) => api.get('/recommendations/wishlist/', { params })
export const createWishlistItem = (data) => api.post('/recommendations/wishlist/', data)
export const updateWishlistItem = (id, data) => api.patch(`/recommendations/wishlist/${id}/`, data)
export const deleteWishlistItem = (id) => api.delete(`/recommendations/wishlist/${id}/`)

// 统计
export const getDashboardOverview = () => api.get('/statistics/overview/')
export const getCirculationRate = (params) => api.get('/statistics/circulation/', { params })
export const getPopularRank = (params) => api.get('/statistics/popular/', { params })
export const getPopularTextbookRank = (params) => api.get('/statistics/popular/', { params })
export const getPriceTrend = (params) => api.get('/statistics/price-trend/', { params })
export const getCollegeDemand = () => api.get('/statistics/college-demand/')
export const getTransactionTypes = () => api.get('/statistics/transaction-types/')
export const getTransactionTypeDist = () => api.get('/statistics/transaction-types/')
export const getUserActivity = (params) => api.get('/statistics/user-activity/', { params })
export const getCategoryDistribution = () => api.get('/statistics/category-distribution/')
export const getSalesRanking = (params) => api.get('/statistics/sales-ranking/', { params })
export const getDemandRanking = (params) => api.get('/statistics/demand-ranking/', { params })
export const getTopSellers = (params) => api.get('/statistics/top-sellers/', { params })
export const getPriceMetrics = (params) => api.get('/statistics/price-metrics/', { params })
export const getWishlistDemand = () => api.get('/statistics/wishlist-demand/')
export const getCancellationInsights = (params) => api.get('/statistics/cancellation-insights/', { params })
export const getUserInsights = (params) => api.get('/statistics/user-insights/', { params })
export const getTopSellersRating = (params) => api.get('/statistics/top-sellers-rating/', { params })
export const getPopularTextbookDetail = (params) => api.get('/statistics/popular-detail/', { params })


// 社区（公告/论坛）
export const getAnnouncements = (params) => api.get('/community/announcements/', { params })
export const getAnnouncementManageList = (params) => api.get('/community/announcements/manage/', { params })
export const createAnnouncement = (data) => api.post('/community/announcements/manage/', data)
export const updateAnnouncement = (id, data) => api.patch(`/community/announcements/manage/${id}/`, data)
export const deleteAnnouncement = (id) => api.delete(`/community/announcements/manage/${id}/`)
export const getForumTopics = (params) => api.get('/community/forum/topics/', { params })
export const createForumTopic = (data) => api.post('/community/forum/topics/', data)
export const getForumTopicDetail = (id) => api.get(`/community/forum/topics/${id}/`)
export const deleteForumTopic = (id) => api.delete(`/community/forum/topics/${id}/`)
export const createForumReply = (topicId, data) => api.post(`/community/forum/topics/${topicId}/replies/`, data)
export const markBestAnswer = (topicId, replyId) => api.post(`/community/forum/topics/${topicId}/best-answer/${replyId}/`)

// 审核 - 别名
export const getSensitiveWordList = (params) => api.get('/reviews/sensitive-words/', { params })

// 用户 - 别名
export const changePasswordApi = (data) => api.post('/users/change-password/', data)
