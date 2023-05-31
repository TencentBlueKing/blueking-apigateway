<template>
  <content-loader
    :width="1240"
    :style="{ 'transform': `scale(${contentWidth / 1615})` }"
    :height="400"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="0" rx="2" ry="2" width="595" height="36" />
    <rect x="0" y="48" rx="2" ry="2" width="300" height="36" />
    <rect x="0" y="96" rx="2" ry="2" width="400" height="36" />
    <rect x="0" y="144" rx="2" ry="2" width="200" height="36" />

    <rect x="620" y="0" rx="2" ry="2" width="595" height="36" />
    <rect x="620" y="48" rx="2" ry="2" width="300" height="36" />
    <rect x="620" y="96" rx="2" ry="2" width="400" height="36" />
    <rect x="620" y="144" rx="2" ry="2" width="200" height="36" />
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
