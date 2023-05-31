<template>
  <router-view :key="renderKey"></router-view>
</template>

<script>
  export default {
    data () {
      return {
        renderKey: 0
      }
    },

    watch: {
      '$route' (newVal, oldVal) {
        console.log(newVal, oldVal)
        if (newVal.name !== oldVal.name) {
          this.renderKey++
        } else if (newVal.params.id !== oldVal.params.id) {
          this.renderKey++
        } else if (newVal.params.hasOwnProperty('version')) {
          if (newVal.params['version'] !== oldVal.params['version']) {
            this.renderKey++
          }
        }
      }
    }
  }
</script>
