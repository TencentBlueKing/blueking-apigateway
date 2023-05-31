<template>
  <content-loader
    :width="baseWidth"
    :height="420"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="103" y="383" rx="2" ry="2" width="73" height="32" />
    <rect x="186" y="383" rx="2" ry="2" width="73" height="32" />
    <rect x="0" y="0" rx="2" ry="2" :width="contentWidth" height="32" />
    <rect x="13" y="62" rx="2" ry="2" width="66" height="20" />
    <rect x="13" y="146" rx="2" ry="2" width="66" height="20" />
    <rect x="13" y="198" rx="2" ry="2" width="66" height="20" />
    <rect x="13" y="253" rx="2" ry="2" width="66" height="20" />
    <rect x="102" y="146" rx="2" ry="2" width="90" height="20" />
    <rect x="103" y="56" rx="2" ry="2" width="650" height="32" />
    <rect x="103" y="193" rx="2" ry="2" width="650" height="32" />
    <rect x="770" y="193" rx="2" ry="2" width="93" height="32" />
    <rect x="103" y="247" rx="2" ry="2" width="650" height="74" />
    <rect x="103" y="331" rx="2" ry="2" width="650" height="32" />
    <rect x="102" y="96" rx="2" ry="2" width="384" height="20" />
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
