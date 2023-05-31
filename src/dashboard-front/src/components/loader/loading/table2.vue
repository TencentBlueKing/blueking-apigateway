<template>
  <content-loader
    :width="1200"
    :height="600"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <!-- table -->
    <rect x="0" y="0" rx="2" ry="2" width="200" height="20" />

    <rect x="0" y="35" rx="2" ry="2" width="90" height="32" />
    <rect x="100" y="35" rx="2" ry="2" width="90" height="32" />

    <rect x="0" y="80" rx="2" ry="2" width="1200" height="40" />
        
    <rect x="0" y="130" rx="2" ry="2" width="250" height="20" />
    <rect x="280" y="130" rx="2" ry="2" width="300" height="20" />
    <rect x="610" y="130" rx="2" ry="2" width="300" height="20" />
    <rect x="950" y="130" rx="2" ry="2" width="250" height="20" />

    <rect x="0" y="170" rx="2" ry="2" width="250" height="20" />
    <rect x="280" y="170" rx="2" ry="2" width="300" height="20" />
    <rect x="610" y="170" rx="2" ry="2" width="300" height="20" />
    <rect x="950" y="170" rx="2" ry="2" width="250" height="20" />

    <rect x="0" y="210" rx="2" ry="2" width="250" height="20" />
    <rect x="280" y="210" rx="2" ry="2" width="300" height="20" />
    <rect x="610" y="210" rx="2" ry="2" width="300" height="20" />
    <rect x="950" y="210" rx="2" ry="2" width="250" height="20" />
        
    <rect x="0" y="250" rx="2" ry="2" width="250" height="20" />
    <rect x="280" y="250" rx="2" ry="2" width="300" height="20" />
    <rect x="610" y="250" rx="2" ry="2" width="300" height="20" />
    <rect x="950" y="250" rx="2" ry="2" width="250" height="20" />

    <rect x="0" y="290" rx="2" ry="2" width="250" height="20" />
    <rect x="280" y="290" rx="2" ry="2" width="300" height="20" />
    <rect x="610" y="290" rx="2" ry="2" width="300" height="20" />
    <rect x="950" y="290" rx="2" ry="2" width="250" height="20" />

    <rect x="0" y="330" rx="2" ry="2" width="250" height="20" />
    <rect x="280" y="330" rx="2" ry="2" width="300" height="20" />
    <rect x="610" y="330" rx="2" ry="2" width="300" height="20" />
    <rect x="950" y="330" rx="2" ry="2" width="250" height="20" />
    <!-- table -->
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
        default: 1615
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
