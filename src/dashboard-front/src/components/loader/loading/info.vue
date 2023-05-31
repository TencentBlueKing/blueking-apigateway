<template>
  <content-loader
    :width="1650"
    :height="516"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="56" y="0" rx="2" ry="2" width="70" height="20" />
    <rect x="56" y="44" rx="2" ry="2" width="70" height="20" />
    <rect x="56" y="88" rx="2" ry="2" width="70" height="20" />
    <rect x="56" y="132" rx="2" ry="2" width="70" height="20" />
    <rect x="56" y="176" rx="2" ry="2" width="70" height="20" />
    <rect x="155" y="176" rx="2" ry="2" width="271" height="20" />
    <rect x="155" y="134" rx="2" ry="2" width="20" height="20" />
    <rect x="155" y="88" rx="2" ry="2" width="52" height="20" />
    <rect x="155" y="46" rx="2" ry="2" width="74" height="20" />
    <rect x="155" y="0" rx="2" ry="2" width="74" height="20" />
    <rect x="482" y="0" rx="2" ry="2" width="70" height="20" />
    <rect x="482" y="44" rx="2" ry="2" width="70" height="20" />
    <rect x="482" y="88" rx="2" ry="2" width="70" height="20" />
    <rect x="584" y="88" rx="2" ry="2" width="221" height="20" />
    <rect x="155" y="88" rx="2" ry="2" width="52" height="20" />
    <rect x="584" y="46" rx="2" ry="2" width="74" height="20" />
    <rect x="584" y="0" rx="2" ry="2" width="74" height="20" />
    <rect x="56" y="220" rx="2" ry="2" width="70" height="20" />
    <rect x="56" y="270" rx="2" ry="2" width="70" height="20" />
    <rect x="56" y="368" rx="2" ry="2" width="70" height="20" />
    <rect x="155" y="270" rx="2" ry="2" width="570  " height="84" />
    <rect x="155" y="368" rx="2" ry="2" width="570  " height="46" />
    <rect x="155" y="420" rx="2" ry="2" width="384" height="19" />
    <rect x="155" y="458" rx="2" ry="2" width="119" height="32" />
    <rect x="291" y="458" rx="2" ry="2" width="74" height="32" />
    <rect x="375" y="458" rx="2" ry="2" width="74" height="32" />
    <rect x="155" y="220" rx="2" ry="2" width="457" height="20" />
    <path d="M 0.5 263.5 h 864" />
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
