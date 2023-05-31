<template>
  <content-loader
    :width="baseWidth"
    :height="690"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="5" rx="2" ry="2" width="95" height="32" />
    <rect x="105" y="5" rx="2" ry="2" width="95" height="32" />
    <rect x="210" y="5" rx="2" ry="2" width="95" height="32" />

    <rect x="100" y="66" rx="2" ry="2" width="60" height="20" />
    <rect x="180" y="60" rx="2" ry="2" :width="width" height="32" />

    <rect x="100" y="120" rx="2" ry="2" width="60" height="20" />
    <rect x="180" y="115" rx="2" ry="2" :width="width" height="32" />

    <rect x="100" y="170" rx="2" ry="2" width="60" height="20" />
    <rect x="180" y="165" rx="2" ry="2" :width="width" height="75" />

    <rect x="70" y="285" rx="2" ry="2" width="90" height="20" />
    <rect x="180" y="280" rx="2" ry="2" :width="width" height="32" />

    <rect x="70" y="340" rx="2" ry="2" width="90" height="20" />
    <rect x="180" y="330" rx="2" ry="2" :width="90" height="32" />
    <rect x="280" y="330" rx="2" ry="2" :width="70" height="32" />

    <rect x="180" y="380" rx="2" ry="2" :width="width" height="170" />
    <rect x="180" y="560" rx="2" ry="2" :width="600" height="20" />

    <rect :x="offsetX" y="595" rx="2" ry="2" :width="120" height="32" />
    <rect :x="offsetX + 130" y="595" rx="2" ry="2" :width="120" height="32" />
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
      menuOpened () {
        return this.$store.state.menuOpened
      },
      loadingConf () {
        return this.$store.state.loadingConf
      },
      width () {
        let width = 1080
        const winWidth = window.innerWidth
        if (this.menuOpened) {
          width = winWidth - 240 - 25 * 2 - 160 - 20 * 2
        }
        return width > 1080 ? 1080 : width
      },
      offsetX () {
        let width = 1080
        const winWidth = window.innerWidth
        if (this.menuOpened) {
          width = winWidth - 240 - 25 * 2 - 160 - 20 * 2
        }
        width = width > 1080 ? 1080 : width
        return width / 2
      }
    }
  }
</script>
