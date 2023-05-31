<template>
  <div class="bk-login-dialog" v-if="isShow">
    <div class="bk-login-wrapper">
      <iframe :src="iframeSrc" scrolling="no" border="0" :width="iframeWidth" :height="iframeHeight"></iframe>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'app-auth',
    data () {
      return {
        iframeSrc: '',
        iframeWidth: 700,
        iframeHeight: 510,
        isShow: false
      }
    },
    methods: {
      hideLoginModal () {
        this.isShow = false
      },
      showLoginModal (data) {
        const callbackUrl = `${location.origin}/static/login_success.html?is_ajax=1`
        const url = `${window.GLOBAL_CONFIG.LOGIN_URL}/plain?size=big&c_url=${callbackUrl}`
        if (!url) {
          console.warn('The response don\'t return login_url')
          return
        }
        this.iframeSrc = url
        const iframeWidth = data.width
        if (iframeWidth) {
          this.iframeWidth = iframeWidth
        }
        const iframeHeight = data.height
        if (iframeHeight) {
          this.iframeHeight = iframeHeight
        }
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
