<template>
  <content-loader
    :width="865"
    :height="1250"
    :speed="loadingConf.speed"
    :primary-color="loadingConf.primaryColor"
    :secondary-color="loadingConf.secondaryColor">
    <rect x="0" y="0" rx="2" ry="2" width="300" height="20" />
    <rect x="0" y="40" rx="2" ry="2" width="260" height="20" />
    <rect x="0" y="76" rx="2" ry="2" width="690" height="42" />

    <rect x="0" y="135" rx="2" ry="2" width="70" height="20" />
    <rect x="0" y="170" rx="2" ry="2" width="50" height="20" />
    <rect x="0" y="205" rx="2" ry="2" width="70" height="20" />
    <rect x="0" y="240" rx="2" ry="2" width="50" height="20" />

    <rect x="120" y="135" rx="2" ry="2" width="150" height="20" />
    <rect x="120" y="170" rx="2" ry="2" width="40" height="20" />
    <rect x="120" y="205" rx="2" ry="2" width="40" height="20" />
    <rect x="120" y="240" rx="2" ry="2" width="40" height="20" />

    <!-- table -->
    <rect x="0" y="300" rx="2" ry="2" width="130" height="20" />
    <rect x="0" y="330" rx="2" ry="2" width="690" height="40" />
        
    <rect x="0" y="385" rx="2" ry="2" width="150" height="20" />
    <rect x="180" y="385" rx="2" ry="2" width="150" height="20" />
    <rect x="360" y="385" rx="2" ry="2" width="150" height="20" />
    <rect x="540" y="385" rx="2" ry="2" width="150" height="20" />

    <rect x="0" y="420" rx="2" ry="2" width="150" height="20" />
    <rect x="180" y="420" rx="2" ry="2" width="150" height="20" />
    <rect x="360" y="420" rx="2" ry="2" width="150" height="20" />
    <rect x="540" y="420" rx="2" ry="2" width="150" height="20" />
    <!-- table -->

    <rect x="0" y="500" rx="2" ry="2" width="130" height="20" />
    <rect x="0" y="535" rx="2" ry="2" width="550" height="20" />

    <!-- table -->
    <rect x="0" y="600" rx="2" ry="2" width="130" height="20" />
    <rect x="0" y="630" rx="2" ry="2" width="690" height="40" />
        
    <rect x="0" y="685" rx="2" ry="2" width="150" height="20" />
    <rect x="180" y="685" rx="2" ry="2" width="150" height="20" />
    <rect x="360" y="685" rx="2" ry="2" width="150" height="20" />
    <rect x="540" y="685" rx="2" ry="2" width="150" height="20" />

    <rect x="0" y="720" rx="2" ry="2" width="150" height="20" />
    <rect x="180" y="720" rx="2" ry="2" width="150" height="20" />
    <rect x="360" y="720" rx="2" ry="2" width="150" height="20" />
    <rect x="540" y="720" rx="2" ry="2" width="150" height="20" />
    <!-- table -->

    <rect x="0" y="770" rx="2" ry="2" width="130" height="20" />
    <rect x="0" y="805" rx="2" ry="2" width="690" height="150" />

    <rect x="0" y="970" rx="2" ry="2" width="130" height="20" />
    <rect x="0" y="1005" rx="2" ry="2" width="690" height="150" />

    <!-- slide -->
    <rect x="730" y="0" rx="2" ry="2" width="1" height="140" />

    <rect x="750" y="0" rx="2" ry="2" width="51" height="15" />
    <rect x="750" y="30" rx="2" ry="2" width="70" height="15" />
    <rect x="750" y="60" rx="2" ry="2" width="51" height="15" />
    <rect x="750" y="90" rx="2" ry="2" width="70" height="15" />
    <!-- slide -->
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
