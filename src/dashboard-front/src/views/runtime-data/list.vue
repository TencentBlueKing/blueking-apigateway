<template>
  <div class="app-content">
    <div class="top-header mb15">
      <strong class="f16" style="color: #63656e; font-weight: normal;"> {{ $t('所有运营系统实时概况') }} </strong>
      <bk-select
        v-model="timeRange"
        :clearable="false"
        :scroll-height="300"
        style="width: 200px; right: 15px;"
        @change="handleTimeChange">
        <bk-option v-for="option in timeList"
          :key="option.id"
          :id="option.id"
          :name="option.name">
        </bk-option>
      </bk-select>
      <div class="filter">
        <div class="auto-refresh">
          <bk-switcher class="mr10" v-model="autoEnable" theme="primary"></bk-switcher><span class="vm f13"> {{ $t('每分钟自动刷新') }} </span>
        </div>
      </div>
    </div>
    <div class="runtime-container mt20" :style="{ height: containerHeight, position: 'relative' }" v-bkloading="{ isLoading: isDataLoading, opacity: 1 }">
      <div class="chart-box" style="position: relative;">
        <template v-if="charts.length">
          <div class="chart-card"
            v-for="(chart, index) of charts"
            :key="index"
            @click="handleGoDetail(chart)">
            <div class="card-content">
              <div class="header">
                <p>{{chart.basic_info.description}} <span class="f12" style="color: #979ba5;">({{chart.basic_info.name}})</span></p>
              </div>
              <div class="wrapper">
                <div class="detail-wrapper">
                  <div class="per_response_time"><strong>{{chart.perc95_resp_time ? chart.perc95_resp_time.value : '0'}}</strong> ms</div>
                  <div class="response_count">{{chart.requests ? chart.requests.count : '0'}} 次</div>
                </div>
                <div class="ring-wrapper">
                  <Ring
                    v-if="chart.rate_availability.value < 1"
                    v-bk-tooltips="$t('可用率低于100%')"
                    :percent="chart.rate_availability.value_str"
                    :size="80"
                    :stroke-width="8"
                    :fill-width="8"
                    :fill-color="initRingColor(chart)"
                    :text-style="initRingTextStyle(chart)">
                  </Ring>
                  <Ring
                    v-else
                    :percent="chart.rate_availability.value_str"
                    :size="80"
                    :stroke-width="8"
                    :fill-width="8"
                    :fill-color="initRingColor(chart)"
                    :text-style="initRingTextStyle(chart)">
                  </Ring>
                </div>
              </div>
            </div>
          </div>
        </template>
        <bk-exception type="empty" scene="part" v-else style="border: 1px solid #eee; border-raidus: 2px; background: #fff; margin-right: 15px;">
          <span>{{ $t('暂无数据') }}</span>
        </bk-exception>
      </div>

      <div class="timeline-box" v-if="statusList.length">
        <bk-timeline :list="statusList"></bk-timeline>
      </div>
    </div>
  </div>
</template>

<script>
  import Ring from '@/components/ring'
  import moment from 'moment'
  import { catchErrorHandler } from '@/common/util'

  moment.locale('zh-cn')

  export default {
    components: {
      Ring
    },
    data () {
      return {
        isDataLoading: true,
        charts: [],
        timelines: [],
        statusList: [],
        timer: 0,
        autoEnable: true,
        containerHeight: '100%',
        timeRange: '1m',
        timeList: [
          { id: '1m', name: this.$t('最近 1 分钟') },
          { id: '10m', name: this.$t('最近 10 分钟') },
          { id: '30m', name: this.$t('最近 30 分钟') },
          { id: '1h', name: this.$t('最近 1 小时') },
          { id: '6h', name: this.$t('最近 6 小时') },
          { id: '12h', name: this.$t('最近 12 小时') },
          { id: '24h', name: this.$t('最近 24 小时') }
        ]
      }
    },
    watch: {
      autoEnable () {
        this.enableAutoRefresh()
      }
    },
    mounted () {
      const winHeight = window.innerHeight - 250
      this.containerHeight = `${winHeight}px`
      this.init()
    },
    beforeDestroy () {
      this.clearAutoRefresh()
    },
    methods: {
      init () {
        this.initData()
        this.enableAutoRefresh()
      },

      initData () {
        this.isDataLoading = true
        Promise.all([this.getRuntime(), this.getTimeline()]).then(res => {
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
        })
      },

      async getRuntime (page) {
        try {
          const res = await this.$store.dispatch('runtime/getApigwRuntime', {
            timeRange: this.timeRange
          })
          this.charts = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getTimeline (page) {
        const apigwId = this.apigwId
        try {
          const res = await this.$store.dispatch('runtime/getApigwTimeline', { apigwId })
          this.timelines = res.data
          this.initTimeline()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      initTimeline () {
        console.log('timelines', this.timelines)
        this.timelines.forEach(item => {
          const time = moment(item.data.mts).fromNow()
          const data = {
            tag: `${item.system_name} ${time}`,
            content: '',
            filled: false
          }

          switch (item.type) {
            case 'errors_occurred':
              data.type = 'warning'
              data.content = this.$t(`偶发 {errorCount} 次请求错误`, { errorCount: item.data.requests.error_count })
              break

            case 'availability_restored':
              data.type = 'success'
              const start = moment(item.mts)
              const end = moment(item.mts_end)

              const timeSpan = end.from(start, true)
              data.content = `<div>可用率恢复至 ${item.data.rate_availability.value_str}%, 低可用持续时间: <strong> ${timeSpan}</strong></div>`
              break

            case 'availability_dropped':
              data.type = 'danger'
              data.content = `<div>可用率下降至 <strong>${item.data.rate_availability.value_str}%</strong>, 调用错误数/总次数: <strong> ${item.data.requests.error_count}/${item.data.requests.count}</strong></div>`
              break
          }
          this.statusList.push(data)
        })
      },

      initRingColor (chart) {
        if (chart.rate_availability.value < 0.97) {
          return '#ff5656'
        } else if (chart.rate_availability.value < 1) {
          return '#ffb848'
        }
        return '#94f5a4'
      },

      initRingTextStyle (chart) {
        if (chart.rate_availability.value < 0.97) {
          return {
            fontSize: '12px',
            color: '#ea3636'
          }
        } else if (chart.rate_availability.value < 1) {
          return {
            fontSize: '12px',
            color: '#ff9c01'
          }
        }
        return {
          fontSize: '12px',
          color: '#2dcb56'
        }
      },

      handleGoDetail (chart) {
        this.$router.push({
          name: 'runtimeDetail',
          params: {
            system: chart.system_name
          },
          query: {
            systemName: chart.basic_info.description
          }
        })
      },

      handleTimeChange (data) {
        this.timeRange = data
        this.initData()
      },

      enableAutoRefresh () {
        clearInterval(this.timer)
        if (!this.autoEnable) {
          return false
        }
        this.timer = setInterval(() => {
          this.initData()
        }, 1000 * 60)
      },

      clearAutoRefresh () {
        clearInterval(this.timer)
      }
    }
  }
</script>
<style lang="postcss" scoped>
    .top-header {
        display: flex;
        height: 32px;
        line-height: 32px;
        color: #63656e;
        align-items: center;

        strong {
            flex: 1;
            font-size: 14px;
        }

        .filter {
            display: flex;
            margin-right: 15px;
        }

        .auto-refresh {
            margin-left: 40px;
            text-align: left;
        }
    }
    .runtime-container {
        min-height: 300px;
        display: flex;

        .chart-box {
            flex: 1;
            display: flex;
            flex-wrap: wrap;
            align-content: flex-start;

            .chart-card {
                flex: 1;
                width: 20%;
                min-width: 20%;
                max-width: 20%;
                height: 155px;

                .card-content {
                    background: #FFF;
                    border-radius: 2px;
                    margin: 0 15px 15px 0;
                    box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.16);
                    display: inline-block;
                    cursor: pointer;
                    display: block;
                }

                .header {
                    font-size: 14px;
                    color: #313238;
                    line-height: 18px;
                    padding: 15px 20px 10px 20px;
                    border-bottom: 1px solid #eee;

                    p {
                        white-space: nowrap;
                        text-overflow: ellipsis;
                        overflow: hidden;
                    }
                }

                .per_response_time {
                    font-size: 16px;
                    text-align: left;
                    color: #63656e;
                    line-height: 32px;
                    margin: 15px 0 5px 0;

                    strong {
                        font-size: 24px;
                        font-weight: bold;
                        color: #63656E;
                    }
                }

                .response_count {
                    font-size: 12px;
                    color: #63656E;
                    line-height: 1;
                }
            }

            .wrapper {
                display: flex;
                padding: 5px 20px 5px 20px;

                .ring-wrapper {
                    width: 80px;
                }

                .detail-wrapper {
                    flex: 1;
                }
            }
        }

        .timeline-box {
            width: 300px;
            height: 100%;
            overflow: auto;
            padding: 0 20px;

            &::-webkit-scrollbar {
                width: 5px;
            }
            &::-webkit-scrollbar-thumb {
                height: 5px;
                border-radius: 2px;
                background-color: #ccc;
            }
        }
        /deep/ .bk-exception {
            height: 280px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        /deep/ .bk-exception-img {
            height: 130px
        }
    }

    @media screen and (max-width: 1920px) {
        .runtime-container .chart-box .chart-card {
            width: 25%;
            min-width: 25%;
            max-width: 25%;
        }

        .timeline-box {
            width: 300px !important;
        }
    }

    @media screen and (max-width: 1680px) {
        .runtime-container .chart-box .chart-card {
            width: 33.3%;
            min-width: 33.3%;
            max-width: 33.3%;
        }

        .timeline-box {
            width: 250px !important;
        }
    }
</style>
