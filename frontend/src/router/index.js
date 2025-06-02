import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path:'/cart',
      name:'cart',
      component: () => import('../views/CartView.vue')
    },
    {
      path:'/orders',
      name:'orders',
      component: () => import('../views/OrdersView.vue')
    },
    {
      path:'/register',
      name:'register',
      component: () => import('../views/RegisterView.vue')
    },
    {
      path:'/login',
      name:'login',
      component: () => import('../views/LoginView.vue')
    },
    {
      path:'/categoryid/:categoryId',
      name:'product',
      component: () => import('../views/ProductView.vue')
    },
    {
      path:'/admin-dashboard',
      name:'admin',
      component: () => import('../views/AdminView.vue')
    },
    {
      path:'/search',
      name:'search',
      component: () => import('../views/SearchView.vue')
    },
  ]
})

export default router
