<script setup>
import Cart from '../components/Cart.vue';
</script>

<template>
  <div class="cart">
    <main>
      <Cart/>
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

