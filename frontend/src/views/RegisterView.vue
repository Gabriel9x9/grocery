<script setup>
import Register from '../components/Register.vue';
</script>

<template>
  <div class="register">
    <main>
      <Register/>
    </main>
  </div>
</template>

<style>
@media (min-width: 1024px) {
  .register {
    min-height: 100vh;
    display: flex;
    align-items: center;
  }
}
</style>
