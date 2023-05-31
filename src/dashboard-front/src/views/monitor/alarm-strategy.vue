<template>
  <div class="app-content">
    <div>
      <alarm-strategy :page-loading.sync="isPageLoading"></alarm-strategy>
    </div>
  </div>
</template>

<script>
  import AlarmStrategy from './children/alarm-strategy'

  export default {
    components: {
      AlarmStrategy
    },
    data () {
      return {
        isPageLoading: true
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      }
    },
    watch: {
      isPageLoading (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.$store.commit('setMainContentLoading', false)
        }
      }
    },
    created () {
    },
    methods: {
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';
</style>
