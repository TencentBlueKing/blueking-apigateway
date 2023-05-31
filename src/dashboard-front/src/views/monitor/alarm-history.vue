<template>
  <div class="app-content">
    <div>
      <alarm-list :page-loading.sync="isPageLoading"></alarm-list>
    </div>
  </div>
</template>

<script>
  import AlarmList from './children/alarm-list'

  export default {
    components: {
      AlarmList
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
