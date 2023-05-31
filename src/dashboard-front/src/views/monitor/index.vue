<template>
  <div class="app-container">
    <div class="app-header">
      {{ $t('监控告警') }}
    </div>
    <div class="app-content" v-bkloading="{ isLoading: isPageLoading, opacity: 1, color: '#f6f7fb' }">
      <bk-tab
        v-show="!isPageLoading"
        :active.sync="tabActive"
        type="unborder-card"
        :ext-cls="'ag-strategy-tab'"
        style="margin-top: -10px;">
        <bk-tab-panel name="alarmStrategy" :label="$t('告警策略')">
          <alarm-strategy v-if="tabActive === 'alarmStrategy'" :page-loading.sync="isPageLoading"></alarm-strategy>
        </bk-tab-panel>
        <bk-tab-panel name="alarmList" :label="$t('告警列表')">
          <alarm-list v-if="tabActive === 'alarmList'"></alarm-list>
        </bk-tab-panel>
      </bk-tab>
    </div>
  </div>
</template>

<script>
  import AlarmStrategy from './children/alarm-strategy'
  import AlarmList from './children/alarm-list'

  export default {
    components: {
      AlarmStrategy,
      AlarmList
    },
    data () {
      return {
        isPageLoading: true,
        tabActive: 'alarmStrategy'
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      }
    },
    created () {
    },
    methods: {
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';
</style>
