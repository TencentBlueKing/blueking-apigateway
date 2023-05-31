<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${contentWidth / baseWidth})` }"
    :height="337"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="0" rx="2" ry="2" width="86" height="32" />
    <rect x="96" y="0" rx="2" ry="2" width="86" height="32" />
    <rect x="192" y="0" rx="2" ry="2" width="86" height="32" />
    <rect x="290" y="0" rx="2" ry="2" width="86" height="32" />

    <rect x="1180" y="0" rx="2" ry="2" width="240" height="32" />
    <rect x="1430" y="0" rx="2" ry="2" width="86" height="32" />
    <rect x="1528" y="0" rx="2" ry="2" width="86" height="32" />

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
