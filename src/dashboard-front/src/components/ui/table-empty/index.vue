<template>
  <div class="paas-table-serch">
    <bk-exception class="exception-wrap-item exception-part" :type="curType" scene="part">
      <div class="exception-part-title">{{ curTitle }}</div>
      <template v-if="curType !== 'empty'">
        <span class="refresh-tips" @click="toRefresh" v-if="abnormal">
          {{$t('刷新')}}
        </span>
        <template v-else>
          <div class="search-empty-tips" v-if="keyword !== '$CONSTANT'">
            {{ $t('可以尝试 调整关键词 或') }}
            <span class="clear-search" @click="handlerClearFilter">
              {{$t('清空搜索条件')}}
            </span>
          </div>
        </template>
      </template>
    </bk-exception>
  </div>
</template>

<script>
  import i18n from '@/language/i18n'
  export default {
    props: {
      keyword: {
        type: String,
        default: ''
      },
      // 是否为暂无数据
      empty: {
        type: Boolean,
        default: false
      },
      // 指定无数据title
      emptyTitle: {
        type: String,
        default: i18n.t('暂无数据')
      },
      // table Ref
      refVal: {
        type: String,
        default: ''
      },
      // 是否为数据异常
      abnormal: {
        type: Boolean,
        default: false
      }
    },
    computed: {
      curType () {
        if (this.abnormal) {
          return '500'
        } else if (!this.empty && this.keyword) {
          return 'search-empty'
        } else {
          return 'empty'
        }
      },
      curTitle () {
        if (this.abnormal) {
          return this.$t('数据获取异常')
        } else if (!this.empty && this.keyword) {
          return this.$t('搜索结果为空')
        } else {
          return this.emptyTitle
        }
      }
    },
    methods: {
      handlerClearFilter () {
        this.$emit('clear-filter', this.refVal)
      },
      toRefresh () {
        this.$emit('clear-filter')
        this.$emit('reacquire')
      }
    }
  }
</script>

<style lang="postcss" scoped>
.paas-table-serch {
    max-height: 280px;
    .search-empty-tips {
        font-size: 12px;
        margin-top: 8px;
        color: #979ba5;
        .clear-search {
            cursor: pointer;
            color: #3a84ff;
        }
    }
    .empty-tips {
        color: #63656e;
    }
    .exception-part-title {
        color: #63656E;
        font-size: 14px;
        margin-bottom: 5px;
    }
    .refresh-tips {
        cursor: pointer;
        color: #3a84ff;
    }
}
</style>
<style lang="postcss">
.paas-table-serch .exception-wrap-item .bk-exception-img.part-img {
    height: 130px;
}
.bk-table-empty-block {
    height: 280px;
    max-height: 280px;
    display: flex;
    align-items: center;
    .bk-table-empty-text {
        padding: 0 !important;
    }
}
</style>
