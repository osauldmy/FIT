import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css'
import 'vue-toast-notification/dist/theme-sugar.css';

import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import VueToast from 'vue-toast-notification';

import App from './App.vue';

Vue.use(BootstrapVue);
Vue.use(VueToast);
Vue.config.productionTip = false;

new Vue({
  render : h => h(App),
}).$mount('#app')
