<template>
  <div class="access-log-container" v-bkloading="{ isLoading: isDataLoading, opacity: 1, color: '#FAFBFD' }">
    <div class="detail-panel" v-show="!isDataLoading && !hasError">
      <div class="panel-hd">
        <h2 class="title" v-html="titleInfo"></h2>
        <small class="time">{{buildTime | formatValue('timestamp')}}</small>
      </div>
      <div class="panel-bd">
        <dl class="details">
          <div class="item" v-for="({ label, field }, index) in details.fields" :key="index">
            <dt class="label">{{label}}</dt>
            <dd class="value">{{details.result[field] | formatValue(field)}}</dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>

<script>
  import { mapState } from 'vuex'
  import { catchErrorHandler } from '@/common/util'
  import dayjs from 'dayjs'

  export default {
    filters: {
      formatValue (value, field) {
        if (value && field === 'timestamp') {
          return dayjs.unix(value).format('YYYY-MM-DD HH:mm:ss')
        }

        return value || '--'
      }
    },
    data () {
      return {
        isDataLoading: false,
        details: {
          fields: [],
          result: {}
        },
        hasError: false
      }
    },
    computed: {
      ...mapState('apis', ['apigwList']),
      apigwId () {
        return this.$route.params.id
      },
      requestId () {
        return this.$route.params.requestId
      },
      queryParams () {
        return this.$route.query
      },
      buildTime () {
        return this.$route.query.bk_timestamp
      },
      currentApigwName () {
        const current = this.apigwList.find(item => item.id === Number(this.apigwId)) || {}
        const name = current.name || ''
        return name
      },
      titleInfo () {
        return this.$t(`蓝鲸应用ID [{detailsAppCode}] 访问API网关 [{currentApigwName}] 资源的请求详情`, { detailsAppCode: this.details.result['app_code'], currentApigwName: this.currentApigwName })
      }
    },
    created () {
      this.getDetailData()
    },
    methods: {
      async getDetailData () {
        const apigwId = this.apigwId
        const requestId = this.requestId
        const params = {
          ...this.queryParams
        }

        this.isDataLoading = true

        try {
          const res = await this.$store.dispatch('accessLog/getApigwAccessLogDetail', { apigwId, requestId, params })

          this.details.result = res.data.results[0] || {}
          this.details.fields = res.data.fields
        } catch (e) {
          catchErrorHandler(e, this)
          this.hasError = true
        } finally {
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';
    .access-log-container {
        width: 1280px;
        min-height: calc(100vh - 138px);
        margin: 0 auto;
        overflow: hidden;
    }

    .detail-panel {
        margin-top: 24px;
        border: 1px solid #EBEDF1;
        background: #fff;

        .panel-bd {
            padding: 16px 0 32px 0;
        }

        .panel-hd {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #EBEDF1;
            padding: 0 30px;

            .title {
                font-size: 22px;
                color: #313238;
                margin: 20px 0;
            }

            .time {
                font-size: 14px;
                color: #C4C6CC;
            }
        }
    }

    .details {
        position: relative;
        padding: 16px 0;
        .item {
            display: flex;
            margin-bottom: 8px;
            font-size: 12px;

            .label {
                position: relative;
                flex: none;
                width: 200px;
                font-weight: bold;
                color: #63656E;
                margin-right: 32px;
                text-align: right;
            }
            .value {
                flex: none;
                width: 500px;
                white-space: pre-wrap;
                word-break: break-word;
                color: #63656E;
                line-height: 20px;
            }
        }

        .share-btn {
            position: absolute;
            right: 0;
            top: 18px;
        }
    }
</style>

<style lang="postcss">
    body {
        background: #FAFBFD !important;
    }
</style>
