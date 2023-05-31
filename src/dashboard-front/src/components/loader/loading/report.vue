<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${contentWidth / baseWidth})` }"
    :height="550"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="6" rx="2" ry="2" width="60" height="20" />
    <rect x="70" y="0" rx="2" ry="2" width="320" height="32" />

    <rect x="400" y="6" rx="2" ry="2" width="40" height="20" />
    <rect x="450" y="0" rx="2" ry="2" width="160" height="32" />

    <rect x="620" y="6" rx="2" ry="2" width="40" height="20" />
    <rect x="670" y="0" rx="2" ry="2" width="260" height="32" />

    <rect x="940" y="6" rx="2" ry="2" width="60" height="20" />
    <rect x="1010" y="0" rx="2" ry="2" width="230" height="32" />

    <rect x="0" y="55" rx="2" ry="2" :width="baseWidth" height="150" />
    <rect x="0" y="220" rx="2" ry="2" :width="baseWidth" height="150" />
    <rect x="0" y="385" rx="2" ry="2" :width="baseWidth" height="150" />

    <!-- <rect x="190" y="6" rx="2" ry="2" width="60" height="20" />
        <rect x="260" y="0" rx="2" ry="2" width="130" height="32" />

        <rect x="410" y="6" rx="2" ry="2" width="80" height="20" />
        <rect x="500" y="0" rx="2" ry="2" width="320" height="32" />
        
        <rect x="1325" y="0" rx="2" ry="2" width="290" height="32" /> -->
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
