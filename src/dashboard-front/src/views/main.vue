<template>
  <div class="app-container">
    <div class="app-header" v-if="!$route.meta.notAppHeader">
      <i class="apigateway-icon icon-ag-return-small" @click="goBack" v-if="$route.meta.parentRoute"></i>
      {{$t($route.meta.title)}}
      <template v-if="syncEsbToApigwEnabled && esb.gateway_id">
        <span v-if="$route.meta.title === $t('组件管理') || $route.meta.title === $t('同步组件配置到 API 网关')" @click="skipPlugin" class="api-link"> {{ $t('（关联的网关资源）') }} </span>
      </template>
      <span v-if="$route.meta.title === $t('组件同步历史')" @click="releaseHistory" class="api-link"> {{ $t('（网关发布历史）') }} </span>
      <div class="apigateway-help-wrapper" v-if="$route.meta.helpLinkList">
        <i class="apigateway-icon icon-ag-help-document"></i>
        <template v-for="(item, index) in $route.meta.helpLinkList">
          <a :key="index" :href="item.url" class="bk-text-button" target="_blank">{{item.text}}</a>
        </template>
      </div>
    </div>
    <ag-loader :loader="$route.meta.loader" :is-loading="mainContentLoading">
      <router-view :key="$route.path" ref="component"></router-view>
    </ag-loader>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  export default {
    data () {
      return {
        syncEsbToApigwEnabled: false,
        esb: {}
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      curApigw () {
        return this.$store.state.curApigw
      },
      routeTitle () {
        return this.$route.meta.title || ''
      },
      mainContentLoading () {
        return this.$store.state.mainContentLoading
      }
    },
    created () {
      this.$store.commit('setMainContentLoading', true)
      this.getFeature()
      if (this.GLOBAL_CONFIG.PLATFORM_FEATURE.MENU_ITEM_ESB_API) {
        this.getEsbGateway()
      }
    },
    methods: {
      goBack () {
        if (this.$refs.component.goBack) {
          this.$refs.component.goBack()
          return
        }
        this.$router.push({
          name: this.$route.meta.parentRoute,
          params: {
            id: this.apigwId
          }
        })
      },
      skipPlugin () {
        const routeData = this.$router.resolve({
          path: `/${this.esb.gateway_id}/resource`
          // name: 'apigwResource'
        })
        window.open(routeData.href, '_blank')
      },
      releaseHistory () {
        const routeData = this.$router.resolve({
          path: `/${this.esb.gateway_id}/release-history`
        })
        window.open(routeData.href, '_blank')
      },
      async getFeature () {
        try {
          const res = await this.$store.dispatch('apis/getFeature')
          this.syncEsbToApigwEnabled = res.data.SYNC_ESB_TO_APIGW_ENABLED
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },
      async getEsbGateway () {
        try {
          const res = await this.$store.dispatch('system/getEsbGateway')
          this.esb = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .api-link,
    .apigateway-help-wrapper i {
        cursor:pointer;
        color: #3a84ff;
        font-size: 12px;
    }
    .apigateway-help-wrapper {
        cursor:pointer;
        font-size: 12px;
    }
</style>
