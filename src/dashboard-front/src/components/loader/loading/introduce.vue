<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${contentWidth / baseWidth})` }"
    :height="337"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="1" y="0" rx="2" ry="2" width="130" height="16" />
    <rect x="0" y="32" rx="2" ry="2" width="200" height="16" />
    <rect x="0" y="64" rx="2" ry="2" width="400" height="16" />
    <rect x="0" y="96" rx="2" ry="2" width="1000" height="16" />
    <rect x="1" y="128" rx="2" ry="2" width="130" height="16" />
    <rect x="0" y="160" rx="2" ry="2" width="200" height="16" />
    <rect x="0" y="202" rx="2" ry="2" width="150" height="50" />
    <rect x="200" y="202" rx="2" ry="2" width="150" height="50" />
    <rect x="400" y="202" rx="2" ry="2" width="150" height="50" />
    <rect x="600" y="202" rx="2" ry="2" width="150" height="50" />
    <rect x="800" y="202" rx="2" ry="2" width="150" height="50" />
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
