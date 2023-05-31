<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${ 1280 / baseWidth})` }"
    :height="337"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="6" rx="2" ry="2" width="120" height="20" />
    <rect x="820" y="0" rx="2" ry="2" width="400" height="32" />
    <rect x="1240" y="0" rx="2" ry="2" width="400" height="32" />

    <rect x="1" y="48" rx="2" ry="2" width="1611" height="42" />
    <rect x="1" y="101" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="144" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="187" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="230" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="273" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="316" rx="2" ry="2" width="355" height="20" />
    <rect x="386" y="101" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="144" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="187" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="230" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="273" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="316" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="101" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="144" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="187" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="230" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="273" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="316" rx="2" ry="2" width="787" height="20" />
    <rect x="1203" y="101" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="144" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="187" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="230" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="273" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="316" rx="2" ry="2" width="410" height="20" />
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
