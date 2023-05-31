<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${contentWidth / baseWidth})` }"
    :height="800"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="0" rx="2" ry="2" width="188" height="32" />
    <rect x="1375" y="0" rx="2" ry="2" width="240" height="32" />

    <rect x="0" y="48" rx="2" ry="2" width="1200" height="372" />
    <rect x="1220" y="48" rx="2" ry="2" width="1" height="372" />
    <rect x="1240" y="48" rx="2" ry="2" width="400" height="372" />
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
