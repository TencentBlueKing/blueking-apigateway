<template>
  <content-loader
    :width="baseWidth"
    :height="600"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor"
    style="position: absolute; left: 50%; top: 0; transform: translate(calc(-25% - 25px));">
    <rect x="0" y="0" rx="2" ry="2" width="800" height="20" />

    <rect x="0" y="36" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="30" rx="2" ry="2" width="690" height="32" />
    <rect x="110" y="68" rx="2" ry="2" width="200" height="20" />

    <rect x="0" y="110" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="103" rx="2" ry="2" width="690" height="32" />

    <rect x="0" y="160" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="158" rx="10" ry="10" width="40" height="26" />

    <rect x="0" y="210" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="210" rx="2" ry="2" width="20" height="20" />

    <rect x="0" y="260" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="254" rx="2" ry="2" width="690" height="32" />
    <rect x="110" y="295" rx="2" ry="2" width="200" height="20" />

    <rect x="0" y="335" rx="2" ry="2" width="800" height="1" />

    <rect x="0" y="360" rx="2" ry="2" width="90" height="20" />
    <rect x="110" y="354" rx="2" ry="2" width="690" height="44" />
    <rect x="110" y="410" rx="2" ry="2" width="690" height="100" />

    <rect x="110" y="520" rx="2" ry="2" width="690" height="32" />

    <rect x="110" y="570" rx="2" ry="2" width="68" height="32" />
    <rect x="190" y="570" rx="2" ry="2" width="68" height="32" />
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
