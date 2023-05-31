<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${contentWidth / baseWidth})` }"
    :height="750"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="0" rx="2" ry="2" :width="baseWidth" height="150" />
    <rect x="0" y="170" rx="2" ry="2" :width="baseWidth" height="150" />
    <rect x="0" y="340" rx="2" ry="2" :width="baseWidth" height="150" />
    <rect x="0" y="510" rx="2" ry="2" :width="baseWidth" height="150" />
    <rect x="740" y="680" width="100" height="32" rx="2"></rect>
    <rect x="855" y="680" width="100" height="32" rx="2"></rect>
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
        default: 1615
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
