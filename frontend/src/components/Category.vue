<script setup>
import WelcomeItem from './WelcomeItem.vue'
</script> 

<template>
  <div style="display: flex; margin-top: 1rem; justify-content: end;">
    <div v-if="isUserRoleAdminOrManager">
      <button @click="productsCSV()" style="color: black; padding: 0.5rem; margin: 0.5rem 0; background-color:white; border-color: #007bff; cursor: pointer;" type="button">EXPORT PRODUCTS CSV</button><br>
      <button @click="inactiveUsersAlert()" style="color: black; padding: 0.5rem; margin: 0.5rem 0; background-color:white; border-color: #007bff; cursor: pointer;" type="button">ALERT: INACTIVE USERS</button>
    </div>
  </div>
  
  <WelcomeItem v-if="isUserRoleAdminOrManager">
    <template #icon>
      <img class="icon" src="https://www.svgrepo.com/show/507823/plus.svg">
    </template>
    <template #heading>New Category Name: </template>
    <input v-model="newCategoryName" type="text" style="padding: 0.5rem;" required placeholder="Enter new category name"><br>
    <div style="font-weight: bold; color: white; font-size: large; margin-top: 0.5rem;">New Category imgURL: </div>
    <input v-model="newCategoryImg" type="text" style="padding: 0.5rem;" placeholder="Enter image URL"><br>
    <button style="padding: 0.5rem; margin: 1rem 0; color: black; background-color:hsla(160, 100%, 37%, 1); cursor: pointer; margin-right: 0.5rem;" @click="addNewCategory">＋ ADD CATEGORY</button>
  </WelcomeItem>

  <WelcomeItem v-for="category in categories" :key="category[0]">
    <template #icon>
      <router-link :to="{ name: 'product', params: {categoryId: category[0] } }">
        <img :src="category[2]" :alt="category[1]" class="categoryIMG" >
      </router-link>
    </template>
    <template #heading>
    <router-link :to="{ name: 'product', params: { categoryId: category[0] } }" style="font-weight: bold; color: white;">
        {{ category[1] }}
      </router-link>
    </template>

    <br/>
    <div v-if="isUserRoleAdminOrManager">
      update Name: <input v-model="updateCategoryName" type="text" style="padding: 0.5rem;" placeholder="Enter new category name"><br>
      update Image-URL: <input v-model="updateCategoryImage" type="text" style="padding: 0.5rem; margin-top: 0.5rem;" placeholder="Enter image URL">
      <br>
      <button style="padding: 0.5rem; margin: 1rem 0; color: white; background-color:#007bff; cursor: pointer; margin-right: 0.5rem;" @click="updateCategory(category[0], category[1])">EDIT</button>
      <button style="padding: 0.5rem; margin: 1rem 0; color: white; background-color:#d43f3a; cursor: pointer;" @click="deleteCategory(category[0], category[1])">DELETE</button>
    </div>
  </WelcomeItem>
</template>

<style>
  .categoryIMG{
    border-radius: 25px;
    width: 10rem;
    height: 10rem;
    padding: 1rem;
  }

@media screen and (max-width: 500px) {
  .icon {
    display: none;
  }

  .categoryIMG {
    display: none;
  }
}
</style>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      userRole:'',
      categories: [],
      updateCategoryName:'',
      updateCategoryImage:''
    };
  },
  computed: {
    isUserRoleAdminOrManager() {
      const userRole = localStorage.getItem('userRole');
      return userRole === 'admin' || userRole === 'manager';
    }
  },
  mounted() {
    this.getUserIdRole();
    this.fetchCategories();
  },
  methods: {
    productsCSV(){
      axios.get(`http://127.0.0.1:4000/export-products-csv`)
      .then(response => {
        axios.get(`http://127.0.0.1:4000/export-products-csv/${response.data.task_id}`, { responseType: 'blob' })
        .then(response => {
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', 'products.csv');
          document.body.appendChild(link);
          link.click();
          link.remove();
        })
        .catch(error => {
          console.error('Error exporting products:', error);
        });
      })
      .catch(error => {
        console.error('Error exporting products:', error);
      });
    },
    inactiveUsersAlert(){
      axios.get(`http://127.0.0.1:4000/alert-inactive-users`)
        .then(response => {
          axios.get(`http://127.0.0.1:4000/alert-inactive-users/${response.data.task_id}`)
          .then(response => {
          })
          .catch(error => {
            console.error('Error sending alert:', error);
          });
        })
        .catch(error => {
          console.error('Error sending alert:', error);
        });
    },
    getUserIdRole(){
      if(localStorage.email!==''){
        axios.get(`http://127.0.0.1:4000/user-idrole/${localStorage.email}`)
        .then((response)=>{
          localStorage.setItem('userId',response.data.userIdRole[0])
          localStorage.setItem('userRole',response.data.userIdRole[1])
        })
        .catch(error => {
            console.error('Get userRole error:', error);
          });
      }
    },
    fetchCategories() {
      axios.get('http://127.0.0.1:4000/')
        .then(response => {
          this.categories = response.data.categories;
        })
        .catch(error => {
          console.error('Error fetching categories:', error);
        });
    },
    addNewCategory() {
      if (this.newCategoryName.trim() !== '') {
        const newCategory = {
          category_name: this.newCategoryName,
          category_img: this.newCategoryImg
        };
        if (localStorage.getItem('userRole') === 'manager') {
          axios.post(`http://127.0.0.1:4000/add-category-request/user=${localStorage.getItem('email')}&role=${localStorage.getItem('userRole')}`, newCategory, {
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
              console.error('Error requesting category:', error);
            });
        } else {
        axios.post('http://127.0.0.1:4000/add-category', newCategory,{
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          })
          .then(response => {
            this.newCategoryName = '';
            this.newCategoryImg = '';
            setTimeout(() => {
              location.reload();
            }, 300);
          })
          .catch(error => {
            console.error('Error adding category:', error);
          });
        }
      }
    },
    updateCategory(categoryId, name){
      const updateCategoryVals={
        updateCategoryName: this.updateCategoryName,
        updateCategoryImage: this.updateCategoryImage
      };
      if (localStorage.getItem('userRole') === 'manager') {
        axios.post(`http://127.0.0.1:4000/edit-category-request/user=${localStorage.getItem('email')}&role=${localStorage.getItem('userRole')}/${categoryId}/${name}`, updateCategoryVals, {
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
            console.error('Error updating category:', error);
          });
      } else {
      axios.post(`http://127.0.0.1:4000/edit-category/${categoryId}`, updateCategoryVals,{
        headers:{
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      .then(()=>{
        setTimeout(() => {
          location.reload();
        }, 300);
        })
      }
  },
    deleteCategory(categoryId, name) {
      axios.post(`http://127.0.0.1:4000/delete-category/user=${localStorage.getItem('email')}&role=${localStorage.getItem('userRole')}/${categoryId}/${name}`)
        .then(() => {
          setTimeout(() => {
            location.reload();
          }, 300);
        })
        .catch(error => {
          console.error('Error deleting category:', error);
        });
    }
  }
};
</script>