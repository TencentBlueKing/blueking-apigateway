<template lang="html">
  <div :class="[{ 'ag-loading-content': isLoaderShow, 'loading': localLoading, 'fadeout': !localLoading }]" :style="{ 'min-height': localLoading && height ? height + 'px' : '100%' }">
    <div :class="['loading-loader', { 'hide': !isLoaderShow }]" :style="{ 'background-color': backgroundColor }">
      <!-- <div :class="['loading-loader', { 'hide': !isLoaderShow }]"> -->
      <template v-if="loader">
        <component
          :is="loader"
          :style="{ 'padding-top': `${offsetTop}px`, 'margin-left': `${offsetLeft}px`, 'transform-origin': 'left top' }"
          :base-width="baseWidth"
          :content-width="contentWidth">
        </component>
      </template>
      <template v-else>
        <div class="bk-loading" style="position: absolute; z-index: 10; background-color: rgba(255, 255, 255, 0.9);">
          <!-- <div class="bk-loading" style="position: absolute; z-index: 10;"> -->
          <div class="bk-loading-wrapper">
            <div class="bk-loading1 bk-colorful bk-size-large">
              <div class="point point1"></div>
              <div class="point point2"></div>
              <div class="point point3"></div>
              <div class="point point4"></div>
            </div>
          </div>
        </div>
      </template>
    </div>
    <slot></slot>
  </div>
</template>

<script>
  import TableLoader from './loading/table'
  // 资源管理
  import ResourceDetailLoader from './loading/resource-detail'
  import ResourceImportLoader from './loading/resource-import'
  import ResourceLoader from './loading/resource'
  import ResourceImportDocLoader from './loading/resource-import-doc'

  // 环境管理
  import StageLoader from './loading/stage'
  import StageDetailLoader from './loading/stage-detail'

  // 访问策略
  import StrategyLoader from './loading/strategy'
  import StrategyDetailLoader from './loading/strategy-detail'

  // 标签管理
  import LabelLoader from './loading/label'

  // 版本
  import VersionLoader from './loading/version'
  import VersionCreateLoader from './loading/version-create'
  import VersionDetailLoader from './loading/version-detail'
  import HistoryLoader from './loading/history'

  // 权限
  import ApplyLoader from './loading/apply'
  import PermissionLoader from './loading/permission'
  import PermissionHistoryLoader from './loading/permission-history'

  // 运行数据
  import ReportLoader from './loading/report'
    
  // 组件管理
  import ComponentManagerLoader from './loading/component-manager'

  // 简介
  import IntroduceLoader from './loading/introduce'

  // 其它
  import IndexLoader from './loading/index'
  import InfoLoader from './loading/info'
  import InfoEditLoader from './loading/info-edit'
  import ApigwCreateLoader from './loading/apigw-create'
  import AlarmHistoryLoader from './loading/alarm-history'
  import TestLoader from './loading/test'
  import SDKLoader from './loading/sdk'
  import AuditLoader from './loading/audit'
  import AccessLogLoader from './loading/access-log'
  import MonitorLoader from './loading/monitor'
  import DiffLoader from './loading/diff'
  import RuntimeChartLoader from './loading/runtime-chart'
  import RuntimeListLoader from './loading/runtime-list'

  // 文档
  import DocLoader from './loading/doc'
  import Table2Loader from './loading/table2'

  export default {
    components: {
      TableLoader,
      ResourceDetailLoader,
      ResourceImportLoader,
      StageLoader,
      ResourceLoader,
      ResourceImportDocLoader,
      StageDetailLoader,
      StrategyLoader,
      LabelLoader,
      InfoLoader,
      InfoEditLoader,
      VersionLoader,
      VersionCreateLoader,
      HistoryLoader,
      PermissionLoader,
      PermissionHistoryLoader,
      ReportLoader,
      AlarmHistoryLoader,
      TestLoader,
      SDKLoader,
      AuditLoader,
      VersionDetailLoader,
      AccessLogLoader,
      IndexLoader,
      MonitorLoader,
      ApigwCreateLoader,
      StrategyDetailLoader,
      ApplyLoader,
      DiffLoader,
      ComponentManagerLoader,
      IntroduceLoader,
      RuntimeChartLoader,
      RuntimeListLoader,
      DocLoader,
      Table2Loader
    },
    props: {
      isLoading: {
        type: Boolean,
        default: true
      },
      loader: {
        type: String
      },
      offsetTop: {
        type: Number,
        default: 25
      },
      offsetLeft: {
        type: Number,
        default: 25
      },
      width: {
        type: Number
      },
      height: {
        type: Number
      },
      delay: {
        type: Number,
        default: 300
      },
      backgroundColor: {
        type: String,
        default: '#f4f7fa'
      }
    },
    data () {
      return {
        localLoading: this.isLoading,
        isLoaderShow: this.isLoading,
        baseWidth: 1615,
        contentWidth: 1280
      }
    },
    computed: {
      menuOpened () {
        return this.$store.state.menuOpened
      }
    },
    watch: {
      isLoading (newVal, oldVal) {
        // true转false时，让loading动画再运行一段时间，防止过快而闪烁
        if (oldVal && !newVal) {
          setTimeout(() => {
            this.localLoading = this.isLoading
            setTimeout(() => {
              this.isLoaderShow = this.isLoading
            }, 200)
          }, this.delay)
        } else {
          this.localLoading = this.isLoading
          this.isLoaderShow = this.isLoading
        }
      },
      menuOpened () {
        this.initContentWidth()
      }
    },
    mounted () {
      this.initContentWidth()

      window.onresize = () => {
        this.initContentWidth()
      }
    },
    methods: {
      initContentWidth () {
        if (this.width) {
          this.contentWidth = this.width
        } else {
          const winWidth = window.innerWidth
          const PADDING_WIDTH = 25
          const MENU_WIDTH = this.menuOpened ? 240 : 60
          this.contentWidth = winWidth - MENU_WIDTH - PADDING_WIDTH * 2
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .ag-loading-content {
        position: relative;
        overflow: hidden;

        &.loading {
            * {
                opacity: 0 !important;
            }
        }

        &.fadeout {
            .loading-loader {
                opacity: 0 !important;
            }
        }

        .loading-loader {
            opacity: 1 !important;
            position: absolute;
            width: 100%;
            height: 100%;
            left: 0;
            right: 0;
            top: 0;
            bottom: 0;
            z-index: 100;
            transition: opacity ease 0.5s;

            &.hide {
                z-index: -1;
            }

            svg {
                width: 1615px;
            }

            * {
                opacity: 1 !important;
            }
        }
    }
    .hide {
        display: none;
    }
</style>
