<template>
  <div class="container">
    <h1 class="m-3">Shopping Cart</h1>
    <table class="table table-bordered p-3 m-3" style="margin: 1rem 0;">
      <thead>
        <tr>
          <th>Product Name</th>
          <th>Price</th>
          <th>Quantity</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="product in productInfo">
          <td>{{ product[3] }}</td>
          <td>₹ {{ product[4] }}</td>
          <td>{{ product[5] }}</td>
          <td>
              <button style="padding: 0.5rem; margin: 1rem 0; color: white; background-color:#d43f3a; border-color: #d43f3a; cursor: pointer; border-radius: 10px;" @click="deleteProduct(product[2], product[5])">DELETE</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div>
      <h3 class="font-weight-bold" style="font-weight: bold; display: flex; justify-content: end;"> Sub Total: ₹ {{ calculateSubtotal() }}</h3>
      <button @click="placeOrder()" style="color: white; font-size: large; padding: 0.5rem; margin: 1rem 0; background-color:#007bff; border-color: #007bff; cursor: pointer;" type="button">Place Order</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      productInfo: [],
    };
  },
  mounted(){
    this.fetchCartData();
  },
  methods: {
    fetchCartData() {
      axios.get(`http://127.0.0.1:4000/cart/${localStorage.getItem('userId')}`)
      .then(response => {
        console.log(response.data)
        this.productInfo = response.data.product_info;
      })
      .catch(error => {
        console.error('Error fetching cart data:', error);
      });
    },
    deleteProduct(productId, quantity) {
      let prod_quantity=0
      
      axios.get(`http://127.0.0.1:4000/product/${productId}`)
      .then(response => {
        prod_quantity=response.data[6]

        const updatedProduct={
          updateProductName:'',
          updateProductImage:'',
          updatePrice:'',
          updateManufacturingDate:'',
          updateExpiryDate:'',
          updateQuantity: prod_quantity+quantity,
          updateUnit:''
      };
      axios.post(`http://127.0.0.1:4000/edit-product/${productId}`, updatedProduct, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          })
          .then(() => {
            axios.post(`http://127.0.0.1:4000/cart/${localStorage.getItem('userId')}/${productId}`)
            .then(response => {
              console.log('Product deleted:', response.data);
              setTimeout(() => {
                location.reload();
              }, 300);
            })
            .catch(error => {
              console.error('Error deleting product:', error);
            });
          })
          .catch(error => {
            console.error('Error updating product:', error);
          });
      })
      .catch(error => {
        console.error('Error fetching product:', error);
      });
    },
    calculateSubtotal() {
      let subtotal = 0;

      for (const product of this.productInfo) {
        subtotal += product[4] * product[5];
      }

      return subtotal.toFixed(2);
    },
    placeOrder() {
      const orderDetails = {
        products: this.productInfo.map(product => ({
          productId: product[2],
          productName: product[3],
          price: product[4],
          quantity: product[5],
        })),
      };

      axios.post(`http://127.0.0.1:4000/placeOrder/${localStorage.getItem('userId')}`, orderDetails,)
        .then(response => {
          console.log('Order placed successfully:', response.data);
          axios.post(`http://127.0.0.1:4000/cart/${localStorage.getItem('userId')}`)
            .then(() => {
              location.reload()
            })
            .catch(error => {
              console.error('Error emptying cart:', error);
            });
        })
        .catch(error => {
          console.error('Error placing order:', error);
        });
    }
  }
};
</script>

<style scoped>
h1 {
  font-weight: bold;
}

th,
td {
  border: solid 0.1rem darkcyan;
  padding: 0.7rem;
}
</style>
