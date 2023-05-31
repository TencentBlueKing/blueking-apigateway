<template>
  <content-loader
    :width="baseWidth"
    :style="{ 'transform': `scaleX(${contentWidth / baseWidth})` }"
    :height="337"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="266" y="2" rx="2" ry="2" width="72" height="32" />
    <rect x="1243" y="2" rx="2" ry="2" width="374" height="32" />
    <rect x="267" y="49" rx="2" ry="2" width="1349" height="42" />
    <rect x="267" y="102" rx="2" ry="2" width="297" height="20" />
    <rect x="267" y="145" rx="2" ry="2" width="297" height="20" />
    <rect x="267" y="188" rx="2" ry="2" width="297" height="20" />
    <rect x="267" y="231" rx="2" ry="2" width="297" height="20" />
    <rect x="267" y="274" rx="2" ry="2" width="297" height="20" />
    <rect x="267" y="317" rx="2" ry="2" width="297" height="20" />
    <rect x="589" y="102" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="145" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="188" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="231" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="274" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="317" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="102" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="145" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="188" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="231" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="274" rx="2" ry="2" width="659" height="20" />
    <rect x="589" y="317" rx="2" ry="2" width="659" height="20" />
    <rect x="0" y="1" rx="2" ry="2" width="240" height="931" />
    <rect x="1274" y="317" rx="2" ry="2" width="343" height="20" />
    <rect x="1274" y="102" rx="2" ry="2" width="343" height="20" />
    <rect x="1274" y="145" rx="2" ry="2" width="343" height="20" />
    <rect x="1274" y="188" rx="2" ry="2" width="343" height="20" />
    <rect x="1274" y="231" rx="2" ry="2" width="343" height="20" />
    <rect x="1274" y="274" rx="2" ry="2" width="343" height="20" />
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
