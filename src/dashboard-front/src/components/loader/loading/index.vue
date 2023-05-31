<template>
  <content-loader
    :width="1280"
    :height="600"
    :style="{ 'transform': `scale(${1280 / baseWidth})` }"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="6" rx="2" ry="2" width="125" height="20" />
    <rect x="880" y="0" rx="2" ry="2" width="90" height="32" />
    <rect x="980" y="0" rx="2" ry="2" width="300" height="32" />

    <rect x="0" y="65" rx="2" ry="2" width="80" height="20" />
    <rect x="260" y="65" rx="2" ry="2" width="60" height="20" />
    <rect x="480" y="65" rx="2" ry="2" width="70" height="20" />
    <rect x="600" y="65" rx="2" ry="2" width="70" height="20" />
    <rect x="780" y="65" rx="2" ry="2" width="70" height="20" />
    <rect x="890" y="65" rx="2" ry="2" width="50" height="20" />

    <rect x="0" y="95" rx="2" ry="2" width="1280" height="85" />
    <rect x="0" y="190" rx="2" ry="2" width="1280" height="85" />
    <rect x="0" y="282" rx="2" ry="2" width="1280" height="85" />
    <rect x="0" y="375" rx="2" ry="2" width="1280" height="85" />
  </content-loader>
</template>

<script>
  import { ContentLoader } from 'vue-content-loader'
  export default {
    components: {
      ContentLoader
    },
    props: {
      baseWidth: {
        type: Number,
        default: 1613
      },
      contentWidth: {
        type: Number,
        default: 1180
      }
    },
    computed: {
      loadingConf () {
        return this.$store.state.loadingConf
      }
    }
  }
</script>
