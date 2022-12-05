<template>
  <div id="app" class="h-100">
    <Navbar />
    <Search />
  </div>
</template>

<script>
import Navbar from "./components/Navbar.vue";
import Search from "./components/Search.vue";

export default {
  name: "App",
  components: {
    Navbar,
    Search
  }
};
</script>
