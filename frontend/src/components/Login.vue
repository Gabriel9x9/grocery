<template>
    <h2>Login</h2>

    <div>
      <label for="email">Email:</label>
      <input type="email" v-model="email" required><br><br>
      
      <label for="password">Password:</label>
      <input type="password" v-model="password" required><br><br>
      
      <button @click="login(email,password)">Login</button>
    </div>

    <p>
      <!-- Don't have an account? <router-link to="/register">Register</router-link> -->
      Don't have an account? <router-link to="/register"><button>Register</button></router-link> 
    </p><br>
    <div style="font-weight: bold;" v-if="loginFailed" class="alert">
      Login failed. Please check your credentials.
    </div>
</template>
  
<script>
import axios from 'axios';

export default {
  data() {
    return {
      email: '',
      password: '',
      loginFailed: false,
    };
  },
  mounted(){

  },
  methods: {
    login(email,password) {
      axios.get(`http://127.0.0.1:4000/login?email=${email}&password=${password}`)
      .then((response)=>{
        if(response.data==='login failed'){
          this.loginFailed = true;
        }else{
          localStorage.setItem('accessToken','Bearer '+response.data.access_token)
          localStorage.setItem('email',email)
          this.email = '';
          this.password = '';
          this.loginFailed = false;
          this.$router.push('/');
          setTimeout(() => {
              location.reload();
            }, 300);
        }
      })
    },
  },
};
</script>
  
<style>
h2 {
  font-weight: bold;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

label {
  font-weight: bold;
}

input[type='email'],
input[type='password'] {
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 1rem;
}

button {
  padding: 0.5rem 1rem;
  background-color: #007bff;
  color: #fff;
  border: none;
  cursor: pointer;
}

p{
  margin-top: 1rem;
}
</style>
  