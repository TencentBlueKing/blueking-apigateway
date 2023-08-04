<template>
  <div class="bk-login-dialog" v-if="isShow">
    <div class="bk-login-wrapper">
      <iframe :src="iframeSrc" scrolling="no" border="0" :width="400" :height="400"></iframe>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'app-auth',
    data () {
      return {
        iframeSrc: '',
        isShow: false
      }
    },
    methods: {
      hideLoginModal () {
        this.isShow = false
      },
      showLoginModal (data) {
        const callbackUrl = `${location.origin}/static/login_success.html?is_ajax=1`
        const loginUrl = window.GLOBAL_CONFIG.LOGIN_URL
        const url = `${loginUrl.endsWith('/') ? loginUrl : `${loginUrl}/`}plain/?c_url=${callbackUrl}`
        if (!url) {
          console.warn('The response don\'t return login_url')
          return
        }
        this.iframeSrc = url
        setTimeout(() => {
          this.isShow = true
        }, 1000)
      }
    }
  }
</script>

<style scoped>
    @import './index.css';
</style>
