<script setup>
import WelcomeItem from './WelcomeItem.vue'
</script>

<template>
  <WelcomeItem v-if="isUserRoleAdminOrManager">
    <template #icon>
      <img class="icon" src="https://www.svgrepo.com/show/507823/plus.svg">
    </template>
    <template #heading>New Product Name</template>
    <input v-model="newProductName" type="text" style="padding: 0.5rem; margin-bottom: 0.3rem;" required placeholder="Enter new product name"><br>
    <div style="font-weight: bold; color: white; font-size: large;">New Product imgURL: </div>
    <input v-model="newProductImg" type="text" style="padding: 0.5rem; margin-bottom: 0.5rem;" required placeholder="Enter new product imgURL"><br>
    Manufacturing Date: 
    <input v-model="manufacturingDate" defaultValue="" type="date" style="padding: 0.5rem; margin-bottom: 0.5rem;"><br>
    Expiry Date:
    <input v-model="expiryDate" defaultValue="" type="date" style="padding: 0.5rem;"><br>
    <div class="price" style="margin-top: 0.5rem; margin-bottom: 0.5rem;">Price: ₹ 
      <input size="4" v-model="price" type="text" style="padding: 0.5rem;" required placeholder="Price"><br></div>
    Quantity: <input v-model="quantity" class="price-input" type="number" min="0" size="3" style="padding: 0.5rem; margin-bottom: 0.5rem;"/><br/>
    Unit: <input v-model="unit" class="price-input" type="text" default="unit" placeholder="unit" min="0" size="4" style="padding: 0.5rem;"/><br/>
    <button class="addToCart" @click="addNewProduct()">＋ Add Product</button>
  </WelcomeItem>

  <WelcomeItem v-for="product in products" :key="product[0]">
    <template #icon>
      <img :src="product[3]" :alt="product[1]" class="categoryIMG" >
    </template>
    <template #heading>{{product[1]}}</template><br/>
    <div v-if="isUserRoleAdminOrManager">
      update Name: <input v-model="updateProductName" type="text" style="padding: 0.5rem;" placeholder="Enter new category name"><br>
      update Image-URL: <input v-model="updateProductImage" type="text" style="padding: 0.5rem; margin-top: 0.5rem; margin-bottom: 0.5rem;" placeholder="Enter image URL"><br>
    </div>
    Manufacturing Date: {{ product[4] }}
    <input v-if="isUserRoleAdminOrManager" v-model="updateManufacturingDate" type="date" style="padding: 0.5rem; margin-bottom: 0.5rem;"><br>
    Expiry Date: {{ product[5] }}
    <input v-if="isUserRoleAdminOrManager" v-model="updateExpiryDate" type="date" style="padding: 0.5rem;"><br>
    <div class="price" style="margin-top: 0.5rem; margin-bottom: 0.5rem;">Price: ₹ {{ product[2] }}
      <input v-if="isUserRoleAdminOrManager" size="4" v-model="updatePrice" type="text" style="padding: 0.5rem;" required placeholder="Price"><br>
    </div>
    Quantity: 
    <input class="quantity" placeholder="1" v-model="prod_quantity" type="number" min="1" :max="product[6]" defaultValue="1" size="3" style="padding: 0.5rem;"/> /
    <input v-if="isUserRoleAdminOrManager" class="quantity" v-model="updateQuantity" type="number" min="0" size="3" style="padding: 0.5rem;"/> <span v-if="product[6] === 0">Out of Stock</span> <span v-else>{{ product[6] }} </span> &nbsp;
    <input v-if="isUserRoleAdminOrManager" class="unit" placeholder="unit" :size="3" v-model="updateUnit" type="text" size="3" style="padding: 0.5rem;"/> {{ product[8] }}
    <br/>
    <div v-if="isUserRoleAdminOrManager">
      <button style="padding: 0.5rem; margin: 1rem 0; color: white; background-color:#007bff; cursor: pointer; margin-right: 0.5rem;" @click="editProduct(product[0], product[1])">EDIT</button>
      <button style="padding: 0.5rem; margin: 1rem 0; color: white; background-color:#d43f3a; cursor: pointer;" @click="deleteProduct(product[0], product[1])">DELETE</button>
    </div>
    <br>
    <button @click="addToCart(product[0], product[1], product[2], product[6])" class="addToCart">Add To Cart</button>
  </WelcomeItem>
</template>

<style>
.addToCart {
  font-weight: bold;
  margin-top: 0.5rem;
  border-radius: 10px;
  padding: 0.5rem 1rem;
  background-color: #007bff;
  color: #fff;
  border: none;
  cursor: pointer;
}
</style>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      prod_quantity: 1,
      categoryId: '',
      products: [],
      updateProductName: '',
      updateProductImage: '',
      updatePrice: '',
      updateManufacturingDate: '',
      updateExpiryDate: '',
      updateQuantity: '',
      updateUnit: ''
    };
  },
  computed: {
    isUserRoleAdminOrManager() {
      const userRole = localStorage.getItem('userRole');
      return userRole === 'admin' || userRole === 'manager';
    }
  },
  mounted() {
    this.categoryId = this.$route.params.categoryId; // Get the category from the route parameter
    this.fetchProducts();
  },
  methods: {
    fetchProducts() {
      axios.get(`http://127.0.0.1:4000/shop_by_category?category_id=${this.categoryId}`)
        .then(response => {
          this.products = response.data.products;
        })
        .catch(error => {
          console.error('Error fetching products:', error);
        });
    },
    addToCart(productId,name,price,quantity) {
      if(localStorage.length===0){
        this.$router.push('/login');
      }
      if (quantity <= 0 || this.prod_quantity>quantity) {
        alert('Sorry, this product is out of stock. Cannot place order.');
        return;
      }
      const data = {
        userId: localStorage.getItem('userId'),
        productId: productId,
        prod_name: name,
        prod_price: price,
        prod_quantity: this.prod_quantity
      };

      const updatedProduct={
        updateProductName: this.updateProductName,
        updateProductImage: this.updateProductImage,
        updatePrice: this.updatePrice,
        updateManufacturingDate: this.updateManufacturingDate,
        updateExpiryDate: this.updateExpiryDate,
        updateQuantity: quantity-this.prod_quantity,
        updateUnit: this.updateUnit
      };

      axios.post('http://127.0.0.1:4000/cart', data,{
        headers:{
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      .then(() => {
        axios.post(`http://127.0.0.1:4000/edit-product/${productId}`, updatedProduct, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          })
          .then(() => {
            setTimeout(() => {
              location.reload();
            }, 300);
          })
          .catch(error => {
            console.error('Error updating product:', error);
          });
      })
      .catch(error => {
        console.error('Error adding product to cart:', error);
      });
    },
    addNewProduct() {
      const newProduct = {
        category_id: this.categoryId,
        product_name: this.newProductName,
        product_img: this.newProductImg,
        product_mft: this.manufacturingDate,
        product_exp: this.expiryDate,
        product_price: this.price,
        product_stock: this.quantity,
        unit: this.unit
      };
      if (this.manufacturingDate > this.expiryDate) {
        alert('Manufacturing date cannot be after the expiry date');
        return;
      }
      if (localStorage.getItem('userRole') === 'manager') {
        axios.post(`http://127.0.0.1:4000/add-product-request/user=${localStorage.getItem('email')}&role=${localStorage.getItem('userRole')}`, newProduct, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          })
          .then(() => {
            this.fetchProducts();
            this.newProductName = '';
            this.newProductImg = '';
            this.manufacturingDate = '';
            this.expiryDate = '';
            this.price = '';
            this.quantity = '';
            this.unit = '';
            setTimeout(() => {
              location.reload();
            }, 300);
          })
          .catch(error => {
            console.error('Error addind product:', error);
          });
      } else {
      axios.post('http://127.0.0.1:4000/add-product', newProduct, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
        .then(response => {
          // Handle successful addition, maybe update the UI or fetch products again
          this.fetchProducts(); // Fetch products again to update the list
          // Reset input fields
          this.newProductName = '';
          this.newProductImg = '';
          this.manufacturingDate = '';
          this.expiryDate = '';
          this.price = '';
          this.quantity = '';
          this.unit = '';
          setTimeout(() => {
              location.reload();
            }, 300);
        })
        .catch(error => {
          console.error('Error adding product:', error);
        });
      }
    },
    editProduct(productId, name) {
      const updatedProduct = {
        updateProductName: this.updateProductName,
        updateProductImage: this.updateProductImage,
        updatePrice: this.updatePrice,
        updateManufacturingDate: this.updateManufacturingDate,
        updateExpiryDate: this.updateExpiryDate,
        updateQuantity: this.updateQuantity,
        updateUnit: this.updateUnit
      };
      if (this.updateManufacturingDate > this.updateExpiryDate) {
        alert('Manufacturing date cannot be after the expiry date');
        return;
      }
      if (localStorage.getItem('userRole') === 'manager') {
        axios.post(`http://127.0.0.1:4000/edit-product-request/user=${localStorage.getItem('email')}&role=${localStorage.getItem('userRole')}/${productId}/${name}`, updatedProduct, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          })
          .then(() => {
            setTimeout(() => {
              location.reload();
            }, 300);
          })
          .catch(error => {
            console.error('Error updating product:', error);
          });
      } else {
        axios.post(`http://127.0.0.1:4000/edit-product/${productId}`, updatedProduct, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          })
          .then(() => {
            setTimeout(() => {
              location.reload();
            }, 300);
          })
          .catch(error => {
            console.error('Error updating product:', error);
          });
      }
    },
    deleteProduct(productId, name) {
      axios.post(`http://127.0.0.1:4000/delete-product/user=${localStorage.getItem('email')}&role=${localStorage.getItem('userRole')}/${productId}/${name}`)
        .then(() => {
          setTimeout(() => {
            location.reload();
          }, 300);
        })
        .catch(error => {
          console.error('Error deleting product:', error);
        });
    }
  }
};
</script>
