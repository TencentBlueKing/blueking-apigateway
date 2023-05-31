<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${contentWidth / baseWidth})` }"
    :height="337"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">

    <rect x="0" y="0" rx="2" ry="2" width="85" height="20" />
    <rect x="110" y="0" rx="2" ry="2" width="85" height="20" />

    <rect x="0" y="30" rx="2" ry="2" :width="baseWidth" height="1" />

    <rect x="0" y="50" rx="2" ry="2" width="88" height="32" />
    <rect x="1375" y="50" rx="2" ry="2" width="240" height="32" />

    <rect x="1" y="98" rx="2" ry="2" width="1611" height="42" />
    <rect x="1" y="150" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="194" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="237" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="280" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="323" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="366" rx="2" ry="2" width="355" height="20" />
    <rect x="386" y="150" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="194" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="237" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="280" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="323" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="366" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="150" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="194" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="237" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="280" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="323" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="366" rx="2" ry="2" width="787" height="20" />
    <rect x="1203" y="150" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="194" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="237" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="280" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="323" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="366" rx="2" ry="2" width="410" height="20" />
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
