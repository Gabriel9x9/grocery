<script setup>
import Orders from '../components/Orders.vue';
</script>

<template>
  <div class="orders">
    <main>
      <Orders/>
    </main>
  </div>
</template>

<style>
@media (min-width: 1024px) {
  .cart {
    min-height: 100vh;
    display: flex;
    align-items: center;
  }
}
</style>

