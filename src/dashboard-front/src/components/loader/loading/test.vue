<template>
  <content-loader
    :width="1642"
    :style="{ 'transform': `scaleX(${contentWidth / 1642})` }"
    :height="1069"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="123" y="783" rx="2" ry="2" width="660" height="32" />
    <rect x="123" y="819" rx="2" ry="2" width="660" height="32" />
    <rect x="123" y="855" rx="2" ry="2" width="660" height="32" />
    <rect x="123" y="928" rx="2" ry="2" width="660" height="32" />
    <rect x="123" y="964" rx="2" ry="2" width="660" height="32" />
    <rect x="123" y="1037" rx="2" ry="2" width="87" height="32" />
    <rect x="220" y="1037" rx="2" ry="2" width="68" height="32" />
    <rect x="123" y="892" rx="2" ry="2" width="530" height="20" />
    <rect x="123" y="1001" rx="2" ry="2" width="422" height="20" />
    <rect x="33" y="42" rx="2" ry="2" width="66" height="20" />
    <rect x="0" y="0" rx="2" ry="2" width="52" height="20" />
    <rect x="33" y="94" rx="2" ry="2" width="66" height="20" />
    <rect x="33" y="166" rx="2" ry="2" width="66" height="20" />
    <rect x="33" y="218" rx="2" ry="2" width="66" height="20" />
    <rect x="122" y="126" rx="2" ry="2" width="268" height="20" />
    <rect x="123" y="36" rx="2" ry="2" width="660" height="32" />
    <rect x="870" y="0" rx="2" ry="2" width="66" height="20" />
    <rect x="870" y="120" rx="2" ry="2" width="66" height="20" />
    <rect x="870" y="162" rx="2" ry="2" width="103" height="20" />
    <rect x="870" y="36" rx="2" ry="2" width="730" height="39" />
    <rect x="123" y="88" rx="2" ry="2" width="660" height="32" />
    <rect x="123" y="160" rx="2" ry="2" width="660" height="32" />
    <rect x="122" y="212" rx="2" ry="2" width="32" height="32" />
    <rect x="33" y="270" rx="2" ry="2" width="66" height="20" />
    <rect x="33" y="320" rx="2" ry="2" width="66" height="20" />
    <rect x="33" y="789" rx="2" ry="2" width="66" height="20" />
    <rect x="33" y="934" rx="2" ry="2" width="66" height="20" />
    <rect x="122" y="264" rx="2" ry="2" width="32" height="32" />
    <rect x="123" y="311" rx="2" ry="2" width="660" height="452" />
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
