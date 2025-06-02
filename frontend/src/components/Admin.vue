<script setup>
import WelcomeItem from './WelcomeItem.vue'
</script> 

<template>
    <WelcomeItem>
    <template #icon>
        <img class="icon" src="https://www.svgrepo.com/show/527954/user-id.svg">
    </template>
    <template #heading>Permission: User Privelege Escalation </template>
    <table>
      <thead>
        <tr>
          <th>User</th>
          <th>Role</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user[0]">
          <td>{{ user[2] }}</td>
          <td>{{ user[5] }}</td>
          <td v-if="user[5] !== 'admin'">
            <button style="padding: 0.5rem; margin: 1rem 0; color: white; background-color:#007bff; cursor: pointer; margin-right: 0.5rem;" @click="changeRole(user[0], user[5])">{{ (user[5] === 'manager' ? 'revoke manager' : 'make manager') }}</button>
            <button style="padding: 0.5rem; margin: 1rem 0; color: white; background-color:#d43f3a; cursor: pointer;" @click="deleteUser(user[0])">DELETE</button>
          </td>
        </tr>
      </tbody>
    </table>
    </WelcomeItem>

    <WelcomeItem>
    <template #icon>
        <img class="icon" src="https://www.svgrepo.com/show/495688/setting-2.svg">
    </template>
    <template #heading>Permission: CRUD operations </template>
    <table>
      <thead>
        <tr>
          <th>User</th>
          <th>Request Type</th>
          <th>ON</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="request in requests" :key="request[0]">
          <td>{{ request[11] }}</td>
          <td>{{ request[1] }}</td>
          <td>{{ request[4] }}</td>
          <td>
            <button @click="approveRequest(request[0])" style="padding: 0.5rem; margin: 1rem 0; color: white; background-color:#007bff; cursor: pointer; margin-right: 0.5rem;">APPROVE</button>
            <button @click="declineRequest(request[0])" style="padding: 0.5rem; margin: 1rem 0; color: white; background-color:#d43f3a; cursor: pointer;">DECLINE</button>
          </td>
        </tr>
      </tbody>
    </table>
    </WelcomeItem>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      users: [],
      requests: [],
    };
  },
  mounted() {
    this.fetchUsers();
    this.fetchRequests();
    this.getUserIdRole();
  },
  methods: {
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
    fetchRequests() {
      axios.get('http://127.0.0.1:4000/requests',{
        headers: {
          Authorization: `${localStorage.getItem('accessToken')}`
        }
      })
        .then(response => {
            this.requests = response.data.requests;
        })
        .catch(error => {
          console.error('Error fetching requests:', error);
        });
    },
    fetchUsers() {
      axios.get('http://127.0.0.1:4000/users',{
        headers: {
          Authorization: `${localStorage.getItem('accessToken')}`
        }
      })
        .then(response => {
            this.users = response.data.users;
        })
        .catch(error => {
          console.error('Error fetching users:', error);
        });
    },
    changeRole(userId, userRole) {
      axios.post(`http://127.0.0.1:4000/change-role/${userId}/${userRole}`,{
        headers:{
          'Content-Type': 'application/x-www-form-urlencoded',
          Authorization: `${localStorage.getItem('accessToken')}`
        }
      })
      .then(() => {
          location.reload();
      })
      .catch(error => {
        console.error('Error updating role:', error);
      });
    },
    deleteUser(userId) {
      axios.post(`http://127.0.0.1:4000/delete-user/${userId}`)
        .then(() => {
            location.reload();
            // console.log(response.data)
            // setTimeout(() => {
            //     location.reload();
            // }, 300);
        })
        .catch(error => {
          console.error('Error deleting user:', error);
        });
    },
    declineRequest(requestId) {
      axios.post(`http://127.0.0.1:4000/decline-request/${requestId}`)
        .then(() => {
          this.fetchRequests();
          setTimeout(() => {
            location.reload();
          }, 300);
        })
        .catch(error => {
          console.error('Error declining request:', error);
        });
    },
    approveRequest(requestId) {
      axios.get(`http://127.0.0.1:4000/get-request/${requestId}`)
      .then(response => {
        const requestData = response.data;
        this.postApprovedData(requestData, requestId);
      })
      .catch(error => {
        console.error('Error fetching request data:', error);
      });
    },
    postApprovedData(requestData, requestId) {
      axios.post('http://127.0.0.1:4000/post-approved-data', requestData)
      .then(() => {
        this.declineRequest(requestId);
      })
      .catch(error => {
        console.error('Error posting data:', error);
      });
    }
  }
};
</script>

<style>
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