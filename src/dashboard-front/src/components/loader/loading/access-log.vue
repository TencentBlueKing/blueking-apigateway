<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${contentWidth / baseWidth})` }"
    :height="800"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="6" rx="2" ry="2" width="40" height="20" />
    <rect x="50" y="0" rx="2" ry="2" width="320" height="32" />

    <rect x="380" y="6" rx="2" ry="2" width="60" height="20" />
    <rect x="450" y="0" rx="2" ry="2" width="150" height="32" />

    <rect x="610" y="6" rx="2" ry="2" width="40" height="20" />
    <rect x="660" y="0" rx="2" ry="2" width="500" height="32" />

    <rect x="1180" y="6" rx="2" ry="2" width="80" height="20" />

    <rect x="0" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="40" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="80" y="180" rx="2" ry="2" width="20" height="70" />
    <rect x="120" y="120" rx="2" ry="2" width="20" height="130" />
    <rect x="160" y="100" rx="2" ry="2" width="20" height="150" />

    <rect x="200" y="180" rx="2" ry="2" width="20" height="70" />
    <rect x="240" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="280" y="210" rx="2" ry="2" width="20" height="40" />
    <rect x="320" y="200" rx="2" ry="2" width="20" height="50" />
    <rect x="360" y="190" rx="2" ry="2" width="20" height="60" />
    <rect x="400" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="440" y="180" rx="2" ry="2" width="20" height="70" />
    <rect x="480" y="120" rx="2" ry="2" width="20" height="130" />
    <rect x="520" y="50" rx="2" ry="2" width="20" height="200" />

    <rect x="560" y="180" rx="2" ry="2" width="20" height="70" />
    <rect x="600" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="640" y="210" rx="2" ry="2" width="20" height="40" />
    <rect x="680" y="200" rx="2" ry="2" width="20" height="50" />
    <rect x="720" y="190" rx="2" ry="2" width="20" height="60" />
    <rect x="760" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="800" y="180" rx="2" ry="2" width="20" height="70" />
    <rect x="840" y="120" rx="2" ry="2" width="20" height="130" />
    <rect x="880" y="70" rx="2" ry="2" width="20" height="180" />

    <rect x="920" y="180" rx="2" ry="2" width="20" height="70" />
    <rect x="960" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="1000" y="210" rx="2" ry="2" width="20" height="40" />
    <rect x="1040" y="200" rx="2" ry="2" width="20" height="50" />
    <rect x="1080" y="190" rx="2" ry="2" width="20" height="60" />
    <rect x="1120" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="1160" y="180" rx="2" ry="2" width="20" height="70" />
    <rect x="1200" y="120" rx="2" ry="2" width="20" height="130" />
    <rect x="1240" y="50" rx="2" ry="2" width="20" height="200" />

    <rect x="1280" y="180" rx="2" ry="2" width="20" height="70" />
    <rect x="1320" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="1360" y="210" rx="2" ry="2" width="20" height="40" />
    <rect x="1400" y="200" rx="2" ry="2" width="20" height="50" />
    <rect x="1440" y="190" rx="2" ry="2" width="20" height="60" />
    <rect x="1480" y="160" rx="2" ry="2" width="20" height="90" />
    <rect x="1520" y="180" rx="2" ry="2" width="20" height="70" />
    <rect x="1560" y="120" rx="2" ry="2" width="20" height="130" />
    <rect x="1600" y="50" rx="2" ry="2" width="20" height="200" />

    <rect x="1640" y="160" rx="2" ry="2" width="20" height="90" />

    <rect x="1" y="270" rx="2" ry="2" :width="baseWidth" height="42" />
    <rect x="1" y="325" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="365" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="410" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="450" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="490" rx="2" ry="2" width="355" height="20" />
    <rect x="1" y="530" rx="2" ry="2" width="355" height="20" />
    <rect x="386" y="325" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="365" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="410" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="450" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="490" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="530" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="325" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="365" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="410" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="450" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="490" rx="2" ry="2" width="787" height="20" />
    <rect x="386" y="530" rx="2" ry="2" width="787" height="20" />
    <rect x="1203" y="325" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="365" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="410" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="450" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="490" rx="2" ry="2" width="410" height="20" />
    <rect x="1203" y="530" rx="2" ry="2" width="410" height="20" />
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
