import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { guest: true }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('../views/ForgotPassword.vue'),
    meta: { guest: true }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('../views/ResetPassword.vue')
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/Home.vue')
      },
      {
        path: 'textbooks',
        name: 'TextbookList',
        component: () => import('../views/TextbookList.vue')
      },
      {
        path: 'textbooks/:id',
        name: 'TextbookDetail',
        component: () => import('../views/TextbookDetail.vue')
      },
      {
        path: 'publish',
        name: 'PublishTextbook',
        component: () => import('../views/PublishTextbook.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'my-textbooks',
        name: 'MyTextbooks',
        component: () => import('../views/MyTextbooks.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('../views/Orders.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('../views/Chat.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'resources',
        name: 'SharedResources',
        component: () => import('../views/Resources.vue')
      },
      {
        path: 'wishlist',
        name: 'Wishlist',
        component: () => import('../views/Wishlist.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'statistics',
        name: 'UserStatistics',
        component: () => import('../views/UserStatistics.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'forum',
        name: 'Forum',
        component: () => import('../views/Forum.vue')
      },
      {
        path: 'user/:id',
        name: 'UserProfile',
        component: () => import('../views/UserProfile.vue')
      },
      // 管理后台路由
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('../views/admin/AdminLayout.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
        redirect: '/admin/dashboard',
        children: [
          {
            path: 'dashboard',
            name: 'Dashboard',
            component: () => import('../views/admin/Dashboard.vue')
          },
          {
            path: 'reviews',
            name: 'ReviewManage',
            component: () => import('../views/admin/ReviewManage.vue')
          },
          {
            path: 'users',
            name: 'UserManage',
            component: () => import('../views/admin/UserManage.vue')
          },
          {
            path: 'categories',
            name: 'CategoryManage',
            component: () => import('../views/admin/CategoryManage.vue')
          },
          {
            path: 'sensitive-words',
            name: 'SensitiveWordManage',
            component: () => import('../views/admin/SensitiveWordManage.vue')
          },
          {
            path: 'statistics',
            name: 'Statistics',
            component: () => import('../views/admin/Statistics.vue')
          }
        ]
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const userStr = localStorage.getItem('user_info')
  const user = userStr ? JSON.parse(userStr) : null

  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresAdmin && user && !['admin', 'superadmin'].includes(user.role)) {
    next({ name: 'Home' })
  } else if (to.meta.guest && token) {
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router
