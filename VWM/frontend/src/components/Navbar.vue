<template>
  <b-navbar toggleable="lg" type="dark" style="background-color: purple;">
    <b-navbar-brand>Boolean model</b-navbar-brand>

    <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>

    <b-collapse id="nav-collapse" is-nav>
      <b-navbar-nav class="ml-auto">
        <b-nav-item exact to="#">Search</b-nav-item>
      </b-navbar-nav>

      <b-navbar-nav class="ml-auto" />
    </b-collapse>
  </b-navbar>
</template>

<style scoped>
* {
  outline: none;
  outline-style: none;
}
</style>
