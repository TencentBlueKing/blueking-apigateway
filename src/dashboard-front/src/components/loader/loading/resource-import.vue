<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${contentWidth / baseWidth})` }"
    :height="700"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="0" rx="2" ry="2" width="225" height="32" />
    <rect x="280" y="6" rx="2" ry="2" width="100" height="20" />
    <rect x="1415" y="6" rx="2" ry="2" width="200" height="20" />
    <rect x="0" y="47" rx="2" ry="2" :width="baseWidth" height="400" />
    <rect x="0" y="467" rx="2" ry="2" width="80" height="32" />
    <rect x="100" y="467" rx="2" ry="2" width="80" height="32" />
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
