<template>
  <div class="home-search">
    <input class="search-input" type="text" v-model="searchQuery">
      <button @click="search()" class="search-btn" >🔍</button>
  </div>
  <br>
  <table>
    <thead>
      <tr>
        <th>Product</th>
        <th>Price</th>
        <th>Mft. Date</th>
        <th>Exp. Date</th>
        <th>Category id</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(result, index) in results" :key="index">
        <td><RouterLink :to="`categoryid/${result[7]}`"> {{ result[1] }}</RouterLink></td>
        <td>{{ result[2] }}</td>
        <td>{{ result[4] }}</td>
        <td>{{ result[5] }}</td>
        <td>{{ result[7] }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      results: [],
      searchQuery: '',
    };
  },
  mounted() {
    this.search();
  },
  methods: {
    search() {
      const formData = new FormData();
      formData.append('search_query', this.searchQuery);

      axios.post('http://127.0.0.1:4000/search', formData)
        .then(response => {
          this.results = response.data.search_results;
        })
        .catch(error => {
          console.error('Error fetching search results:', error);
        });
    },
  },
};
</script>

<style>
.home-search{
  display: flex;
  align-items: flex-start;
  margin-top: 1rem;
}

label {
  font-weight: bold;
}

.search-input[type='text'] {
  width: 100%;
  padding: 0.5rem;
  border-radius: 25px;
}

.search-btn {
  margin-left: 1rem;
  border-radius: 25px;
  padding: 0.5rem 1rem;
  background-color: #007bff;
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: large;
}

ul {
  list-style: none;
  padding: 0;
}

li {
  margin-bottom: 0.5rem;
}

a {
  text-decoration: none;
  color: #007bff;
}

table {
  border-collapse: collapse;
  width: 100%;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

</style>
