<template>
  <div class="gateways-empty-table-search">
    <bk-exception class="exception-wrap-item exception-part" :type="curType" scene="part">
      <div class="exception-part-title">{{ curTitle }}</div>
      <template v-if="curType !== 'empty'">
        <span class="refresh-tips" @click="handleRefresh" v-if="abnormal">
          {{ t('刷新') }}
        </span>
        <template v-else>
          <div class="search-empty-tips" v-if="keyword !== '$CONSTANT'">
            {{ t('可以尝试 调整关键词 或') }}
            <span class="clear-search" @click="handlerClearFilter">
              {{ t('清空搜索条件') }}
            </span>
          </div>
        </template>
      </template>
    </bk-exception>
  </div>
</template>

<script lang="ts" setup>
import i18n from '@/language/i18n';
import { computed } from 'vue';

const { t } = i18n.global;

const props = defineProps({
  keyword: {
    type: String,
    default: '',
  },
  empty: {
    type: Boolean,
    default: false,
  },
  emptyTitle: {
    type: String,
    default: i18n.global.t('暂无数据'),
  },
  refVal: {
    type: String,
    default: '',
  },
  abnormal: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['clear-filter', 'reacquire']);

const curType = computed(() => {
  if (props.abnormal) {
    return '500';
  } if (!props.empty && props.keyword) {
    return 'search-empty';
  }
  return 'empty';
});

const curTitle = computed(() => {
  if (props.abnormal) {
    return t('数据获取异常');
  }
  if (!props.empty && props.keyword) {
    return t('搜索结果为空');
  }
  return props.emptyTitle;
});


const handlerClearFilter = () => {
  emit('clear-filter', props.refVal);
};

const handleRefresh = () => {
  emit('clear-filter');
  emit('reacquire');
};
</script>

<style lang="scss" scoped>
.gateways-empty-table-search {
    max-height: 280px;
    width: auto !important;
    display: flex;
    align-items: center;
    margin: 0 auto;

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

    .exception-wrap-item .bk-exception-img.part-img {
        height: 130px;
    }

    .bk-table-empty-text {
        padding: 0 !important;
    }
}
</style>

