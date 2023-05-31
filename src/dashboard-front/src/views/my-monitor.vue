<template>
  <ag-loader
    class="my-monitor-container"
    :is-loading="isPageLoading"
    :loader="'monitor-loader'"
    :offset-top="0"
    :offset-left="0">
    <section class="header clearfix">
      <h3 class="title fl"> {{ $t('我的告警') }} </h3>
      <div class="filters fr">
        <bk-date-picker
          v-model="dateTimeRange"
          :shortcuts="datepickerShortcuts"
          :type="'datetimerange'"
          :shortcut-close="true"
          :use-shortcut-text="true"
          :clearable="false"
          :shortcut-selected-index="shortcutSelectedIndex"
          @shortcut-change="handleShortcutChange"
          @pick-success="handleTimeChange">
        </bk-date-picker>
        <bk-input
          style="width: 300px; display: inline-block; margin-left: 12px;"
          :placeholder="$t('输入网关名称，按Enter搜索')"
          :clearable="true"
          :right-icon="'bk-icon icon-search'"
          v-model="keyword"
          @clear="handleSearch"
          @enter="handleSearch">
        </bk-input>
      </div>
    </section>
    <section class="ap-content">
      <div class="api-alarm-list" v-bkloading="{ isLoading: isDataLoading, color: '#f5f7fb', opacity: 1 }">
        <div class="api-alarm-item" v-for="alarm of alarmList" :key="alarm.api_id">
          <div class="row-api">
            <div class="logo" @click="handleGoPage('apigwResource', alarm)">{{alarm.api_name[0].toUpperCase()}}</div>
            <div class="name" @click="handleGoPage('apigwResource', alarm)">
              {{alarm.api_name}}
            </div>
            <div :class="['stat', { slide: (slideStatus[alarm.api_id] || false) }]" @click="handleStatClick(alarm.api_id)">
              {{ $t('告警次数') }} ({{alarm.alarm_record_count}})
              <i class="apigateway-icon icon-ag-down-small"></i>
            </div>
            <div class="more" @click="handleGoPage('apigwMonitorAlarmHistory', alarm)">
              {{ $t('更多') }} <i class="apigateway-icon icon-ag-jump"></i>
            </div>
          </div>
          <div :class="['row-summary', { slide: (slideStatus[alarm.api_id] || false) }]">
            <div class="row-summary-inner">
              <bk-table
                :data="alarm.strategy_summary"
                :outer-border="false"
                :header-border="false">
                <div slot="empty">
                  <table-empty empty />
                </div>
                <bk-table-column :label="$t('告警策略')" width="220" prop="name" :render-header="$renderHeader"></bk-table-column>
                <bk-table-column :label="$t('告警次数')" width="110" prop="alarm_record_count" :render-header="$renderHeader"></bk-table-column>
                <bk-table-column :label="$t('最近一次告警开始时间')" width="200" prop="latest_alarm_record.created_time" :render-header="$renderHeader"></bk-table-column>
                <bk-table-column :label="$t('最近一次告警内容')" prop="latest_alarm_record.message" :render-header="$renderHeader"></bk-table-column>
              </bk-table>
            </div>
          </div>
        </div>
        <div class="ap-nodata" v-if="!alarmList.length">
          <table-empty empty />
        </div>
      </div>
    </section>
  </ag-loader>
</template>

<script>
  import { mapGetters } from 'vuex'
  export default {
    data () {
      return {
        alarmList: [],
        keyword: '',
        isDataLoading: true,
        isPageLoading: true,
        dateTimeRange: [],
        shortcutSelectedIndex: 4,
        searchParams: {
          time_start: '',
          time_end: ''
        },
        slideStatus: {}
      }
    },
    computed: {
      ...mapGetters('options', ['datepickerShortcuts'])
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getAlarmList()
      },

      async getAlarmList () {
        this.setSearchTimeRange()
        const params = {
          ...this.searchParams,
          query: this.keyword
        }
        try {
          this.isDataLoading = true
          const res = await this.$store.dispatch('monitor/getAlarmList', { params })
          this.alarmList = res.data
        } catch (e) {
          this.$bkMessage({
            theme: 'error',
            message: e.message || this.$t('接口异常')
          })
        } finally {
          this.isDataLoading = false
          this.isPageLoading = false
        }
      },

      setSearchTimeRange () {
        let timeRange = this.dateTimeRange

        // 选择的是时间快捷项，需要实时计算时间值
        if (this.shortcutSelectedIndex !== -1) {
          timeRange = this.datepickerShortcuts[this.shortcutSelectedIndex].value()
        }
        const formatTimeRange = this.formatDatetime(timeRange)
        this.searchParams.time_start = formatTimeRange[0]
        this.searchParams.time_end = formatTimeRange[1]
      },

      formatDatetime (timeRange) {
        return [
          (+new Date(`${timeRange[0]}`)) / 1000,
          (+new Date(`${timeRange[1]}`)) / 1000
        ]
      },

      handleShortcutChange (value, index) {
        this.shortcutSelectedIndex = index
      },

      handleTimeChange () {
        this.getAlarmList()
      },

      handleSearch (event) {
        this.getAlarmList()
      },

      handleApigwInfo (apigw) {
        this.$router.push({
          name: 'apigwInfo',
          params: {
            id: apigw.id
          }
        })
      },

      handleStatClick (id) {
        this.$set(this.slideStatus, id, !this.slideStatus[id])
      },

      handleGoPage (routeName, apigw) {
        this.$router.push({
          name: routeName,
          params: {
            id: apigw.api_id
          }
        })
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';
    @import '@/css/mixins/ellipsis.css';

    .my-monitor-container {
        width: 1280px;
        background: transparent;
        border: none;
        margin: 30px auto 0 auto;
        box-shadow: none;
        overflow: hidden;

        .ap-nodata {
            margin-top: 120px;
            font-size: 12px;
            .bk-table-empty-icon {
                font-size: 65px;
            }
        }
    }

    .header {
        overflow: hidden;
        margin-bottom: 20px;

        .filters {
            --long-width: 320px;
            display: flex;
            align-items: center;
        }

        .title {
            font-weight: normal;
            color: #313238;
            padding: 0;
            margin: 0;
            line-height: 32px;
            font-size: 20px;
        }
    }

    .api-alarm-list {
        font-size: 14px;

        .api-alarm-item {
            background: #fff;
            border-radius: 2px;
            border: 1px solid #dcdee5;
            margin-bottom: 10px;
            padding: 8px 12px;

            .row-api {
                display: flex;
                align-items: center;
            }

            .row-summary {
                .row-summary-inner {
                    margin-top: 16px;
                }

                height: 0;
                opacity: 0;
                transition: all .2s linear;
                overflow: hidden;

                &.slide {
                    opacity: 1;
                    height: 100%;
                }
            }

            &:hover {
                box-shadow: 0px 1px 3px 0px rgba(0, 0, 0, 0.15);
            }

            .logo {
                width: 50px;
                height: 50px;
                text-align: center;
                line-height: 50px;
                background: #AAC8EF;
                color: #FFF;
                font-size: 26px;
                font-weight: bold;
                border-radius: 4px;
                cursor: pointer;
            }
            .name {
                width: 320px;
                margin: 0 12px;
                padding: 12px 0;
                font-weight: bold;
                @mixin ellipsis;
                cursor: pointer;
                &:hover {
                    color: #3a84ff;
                }
            }
            .stat {
                color: #ff4d4d;
                flex: 1;
                padding: 6px 0;
                cursor: pointer;
                .icon-ag-down-small {
                    display: none;
                    color: #3a84ff;
                    font-size: 18px;
                    transition: all .2s ease-out;
                }
                &:hover {
                    .icon-ag-down-small {
                        display: inline-block;
                    }
                }
                &.slide {
                    .icon-ag-down-small {
                        transform: rotate(-180deg);
                    }
                }
            }
            .more {
                color: #3a84ff;
                margin-left: auto;
                margin-right: 50px;
                cursor: pointer;

                &:hover {
                    color: #699df4;
                }
            }
        }
    }

    @media screen and (max-width: 1280px) {
        .my-monitor-container {
            width: 1240px;
        }
    }
</style>
