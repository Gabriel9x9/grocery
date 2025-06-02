<template>
  <div class="container">
    <h1 class="m-3">Orders</h1>
    <table class="table table-bordered p-3 m-3" style="margin: 1rem 0;">
      <thead>
        <tr>
          <th>Product Name</th>
          <th>Price</th>
          <th>Quantity</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="order in orders">
          <td>{{ order[2] }}</td>
          <td>₹ {{ order[3] }}</td>
          <td>{{ order[4] }}</td>
        </tr>
      </tbody>
    </table>
    <div>
      <h3 class="font-weight-bold" style="font-weight: bold; display: flex; justify-content: end;"> Sub Total: ₹ {{ calculateSubtotal() }}</h3>
      <select v-model="selectedMonth" style="padding: 0.5rem; margin-right: 1rem;">
        <option v-for="(month, index) in lastThreeMonths" :key="index" :value="month">{{ month }}</option>
      </select>
      <button @click="exportCSV()" style="color: black; padding: 0.5rem; margin: 0.5rem 0; background-color:white; border-color: #007bff; cursor: pointer;" type="button">export monthly activity</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth() + 1; // JavaScript months are zero-based
    const currentYear = currentDate.getFullYear();

    const lastThreeMonths = [];
    for (let i = 0; i < 3; i++) {
      const month = currentMonth - i;
      const year = month <= 0 ? currentYear - 1 : currentYear;
      const correctedMonth = ((month - 1) % 12) + 1;
      const monthYearString = `${correctedMonth}/${year}`;
      lastThreeMonths.push(monthYearString);
    }

    return {
      orders: [],
      selectedMonth: lastThreeMonths[1],
      lastThreeMonths: lastThreeMonths.reverse()
    };
  },
  mounted(){
    this.fetchOrdersData();
  },
  methods: {
    fetchOrdersData() {
      axios.get(`http://127.0.0.1:4000/orders/${localStorage.getItem('userId')}`)
      .then(response => {
        this.orders = response.data.orders;
      })
      .catch(error => {
        console.error('Error fetching order data:', error);
      });
    },
    calculateSubtotal() {
      let subtotal = 0;

      for (const order of this.orders) {
        subtotal += order[3] * order[4];
      }

      return subtotal.toFixed(2);
    },
    exportCSV() {
      axios.post('http://127.0.0.1:4000/initiate-export-orders', {
        email: localStorage.getItem('email'),
        userId: localStorage.getItem('userId'),
        selectedMonth: this.selectedMonth,
      })
        .then(response => {
          const taskId = response.data.task_id;
          this.checkTaskStatus(taskId);
        })
        .catch(error => {
          console.error('Error initiating export orders:', error);
        });
    },
    checkTaskStatus(taskId) {
      axios.get(`http://127.0.0.1:4000/export-orders-status/${taskId}`)
        .then(response => {
          const taskStatus = response.data.task_status;
          if (taskStatus === 'SUCCESS') {
            this.exportOrders(this.selectedMonth);
          } else if (taskStatus === 'FAILURE') {
          } else {
            console.log('Task is still processing...');
          }
        })
        .catch(error => {
          console.error('Error checking export orders status:', error);
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
