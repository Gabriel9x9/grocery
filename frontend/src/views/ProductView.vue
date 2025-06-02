<script setup>
import Product from '../components/Product.vue';
</script>

<template>
  <div class="product">
    <main>
      <Product/>
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

