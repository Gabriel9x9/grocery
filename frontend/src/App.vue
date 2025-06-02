<script setup>
import { RouterLink, RouterView } from 'vue-router'
import HelloWorld from './components/HelloWorld.vue'
</script>

<template>
  <header>
    <div class="wrapper">
      <RouterLink to="/">
        <HelloWorld msg="🛒 Grocery Store" />
      </RouterLink>
      <nav style="font-size: larger;"><span v-if="userRole !== 'null' && userRole !== 'user'">UserRole: {{ userRole }}</span></nav>
      <nav>
          <RouterLink v-if="isUserRoleAdmin" to="/admin-dashboard">Admin-Dashboard</RouterLink>
          <RouterLink to="/search">Search</RouterLink>
        </nav>
        <nav>
          <RouterLink to="/">Home</RouterLink>
          <RouterLink :to="localStorageLength === 0 ? '/login' : '/cart'">Cart</RouterLink>
          <RouterLink v-if="localStorageLength !== 0" to="/orders">Orders</RouterLink>
        </nav>
        <nav>
          <RouterLink v-if="localStorageLength === 0" to="/register">Register</RouterLink>
          <RouterLink v-if="localStorageLength === 0" to="/login">Sign In</RouterLink>
          <RouterLink v-else to="/logout" @click="logOut()">Log Out</RouterLink>
        </nav>
    </div>
  </header>

  <RouterView />
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      userRole: localStorage.getItem('userRole'),
    };
  },
  computed: {
    isUserRoleAdmin() {
      const userRole = localStorage.getItem('userRole');
      return userRole === 'admin';
    },
    localStorageLength() {
      return Object.keys(localStorage).length;
    }
  },
  mounted(){
    
  },
  methods: {
    logOut() {
      if(localStorage.accessToken){
        axios.get("http://127.0.0.1:4000/logout",{
          headers:{
            'Authorization':localStorage.accessToken
          }
        })
        .then(()=>{
          localStorage.clear()
          this.$router.push('/');
          setTimeout(() => {
            location.reload();
          }, 300);
        })
      } else this.$router.push('/');
    },
    redirectToCartOrLogin() {
      if (this.localStorageLength === 0) {
        this.$router.push('/login');
      } else {
        this.$router.push('/cart');
      }
    }
  },
};
</script>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 1rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1.1rem;

    padding: 0.5rem 0;
    margin-top: 1rem;
  }
}
</style>
