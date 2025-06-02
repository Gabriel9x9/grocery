<script setup>
import Login from '../components/Login.vue';
</script>

<template>
  <div class="login">
    <main>
      <Login/>
    </main>
  </div>
</template>

<style>
@media (min-width: 1024px) {
  .login {
    min-height: 100vh;
    display: flex;
    align-items: center;
  }
}
</style>