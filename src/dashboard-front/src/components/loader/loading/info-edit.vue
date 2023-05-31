<template>
  <content-loader
    :width="baseWidth"
    :height="600"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="6" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="0" rx="2" ry="2" width="690" height="32" />
    <rect x="110" y="38" rx="2" ry="2" width="200" height="20" />

    <rect x="0" y="80" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="73" rx="2" ry="2" width="690" height="32" />

    <rect x="0" y="130" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="128" rx="10" ry="10" width="40" height="26" />

    <rect x="0" y="180" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="180" rx="2" ry="2" width="20" height="20" />

    <rect x="0" y="230" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="224" rx="2" ry="2" width="690" height="32" />
    <rect x="110" y="265" rx="2" ry="2" width="200" height="20" />

    <rect x="0" y="305" rx="2" ry="2" width="800" height="1" />

    <rect x="0" y="330" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="324" rx="2" ry="2" width="690" height="44" />
    <rect x="110" y="380" rx="2" ry="2" width="690" height="100" />

    <rect x="110" y="490" rx="2" ry="2" width="690" height="32" />

    <rect x="110" y="540" rx="2" ry="2" width="68" height="32" />
    <rect x="190" y="540" rx="2" ry="2" width="68" height="32" />
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
