<template>
  <div
    class="apigw-api-sys-filter"
    ref="filterRef">
    <div style="height: 100%">
      <section style="padding: 0 10px;">
        <bk-input
          ext-cls="system-input-cls"
          :placeholder="t('请输入系统名称、描述')"
          v-model="searchValue"
          clearable
          right-icon="bk-icon icon-search"
          @input="handleSearch">
        </bk-input>
      </section>
      <div class="system-list">
        <template v-if="curList.length > 0">
          <div :class="['item all-item', { active: curSelect === '*' }]" @click="handleSelectAll">
            <p class="name all-wrapper">
              <i class="apigateway-icon icon-ag-zonghe"></i>
              <span>{{ t('全部系统') }}</span>
              <span class="all-count fr">
                <span class="count">{{ allCount }}</span>
              </span>
            </p>
          </div>
          <div class="line"></div>
          <div
            v-for="(item, index) in curList"
            :key="index"
            :class="['item set-pf', { active: curSelect === item.id }]"
            @click="handleSelectSys(item)">
            <p class="name">
              <span class="title-wrapper">
                <!-- eslint-disable-next-line vue/no-v-html -->
                <span v-html="highlight(item)"></span>
              </span>
              <span v-if="item.is_official" class="tag">
                {{ t('官方') }}
              </span>
              <span class="count fr">{{ item.component_count }}</span>
            </p>
            <!-- eslint-disable-next-line vue/no-v-html -->
            <p class="desc" v-html="highlightDesc(item)"></p>
          </div>
        </template>
        <template v-else>
          <div class="empty-wrapper">
            <TableEmpty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @clear-filter="clearFilterKey"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import _ from 'lodash';
import { ref, reactive, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();

const props = defineProps({
  list: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits<(e: 'on-select', value: any) => void>();

const curList = ref<any>([]);
const searchValue = ref<string>('');
const curSelect = ref<string>('*');
const isFilter = ref<boolean>(false);
const tableEmptyConf = reactive({
  keyword: '',
  isAbnormal: false,
});

const allCount = computed(() => {
  return curList.value?.reduce((accumulator: number, current: any) => {
    return accumulator + current.component_count;
  }, 0);
});

const updateTableEmptyConfig = () => {
  if (searchValue.value && !curList.value.length) {
    tableEmptyConf.keyword = 'placeholder';
    return;
  }
  if (searchValue.value.length) {
    tableEmptyConf.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.keyword = '';
};

const handleSearch = _.debounce((payload) => {
  if (payload === '') {
    return;
  }
  isFilter.value = true;
  curList.value = props.list?.filter((item: any) => {
    const regex = new RegExp(`(${payload})`, 'gi');
    return (!!item?.name?.match(regex)) || (!!item?.description?.match(regex));
  });
  updateTableEmptyConfig();
});

const handleSelectSys = (payload: any) => {
  curSelect.value = payload?.id;
  emit('on-select', payload);
};

const setSelected = (id: string) => {
  curSelect.value = id;
  emit('on-select', { id });
};

const handleSelectAll = () => {
  curSelect.value = '*';
  emit('on-select', { id: '*' });
};

const highlight = (item: any) => {
  if (!item?.name) {
    return '--';
  }
  const regex = new RegExp(`(${searchValue.value})`, 'gi');
  return item?.name?.replace(regex, '<sysmark>$1</sysmark>');
};

const highlightDesc = (item: any) => {
  if (!item?.description) {
    return t('暂无描述');
  }
  if (item.description !== '' || item.description !== null) {
    const regex = new RegExp(`(${searchValue.value})`, 'gi');
    return item?.description?.replace(regex, '<sysmark>$1</sysmark>');
  }
  return t('暂无描述');
};

const clearFilterKey = () => {
  searchValue.value = '';
};

watch(
  () => props.list,
  (value) => {
    curList.value = [...value];
  },
  {
    immediate: true,
  },
);

watch(
  () => searchValue.value,
  (newVal, oldVal) => {
    if (newVal === '' && oldVal !== '' && isFilter.value) {
      isFilter.value = false;
      curList.value = [...props.list];
    }
  },
);

defineExpose({
  setSelected,
  updateTableEmptyConfig,
});
</script>

<style lang="scss" scoped>
.apigw-api-sys-filter {
  height: 100%;
  color: #63656e;
  .apigw-badge {
    min-width: 30px;
    height: 18px;
    background: #f0f1f5;
    border-radius: 2px;
    font-size: 12px;
    text-align: left;
    color: #979ba5;
    display: inline-block;
    line-height: 18px;
    text-align: center;
    padding: 0 5px;
  }
  .system-list {
    position: relative;
    margin-top: 6px;
    height: 100%;
    overflow-y: auto;
    padding-bottom: 40px;
    &::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    &::-webkit-scrollbar-thumb {
      background: #dcdee5;
      border-radius: 3px;
    }
    &::-webkit-scrollbar-track {
      background: transparent;
      border-radius: 3px;
    }
    .item {
      position: relative;
      padding: 4px 16px;
      height: 48px;
      text-align: left;
      overflow: hidden;
      cursor: pointer;
      &.all-item {
        padding: 0 16px;
      }
      &:hover {
        background: #e1ecff;
        .name {
            color: #3a84ff;
        }
        .all-wrapper i {
            color: #3a84ff !important;
        }
        .count {
            background: #A3C5FD;
            color: #fff;
        }
      }
      &.active {
        background: #e1ecff;
        .name {
            color: #3a84ff;
        }
        .all-wrapper i {
            color: #3a84ff !important;
        }
      }
      .name {
        max-width: 268px;
        font-size: 14px;
        text-align: left;
        color: #63656e;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;

        .title-wrapper {
          max-width: 192px;
          display: inline-block;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        &.all-wrapper {
          line-height: 48px;
          i {
            color: #979ba5;
            position: relative;
            top: -1px;
          }
        }
      }
      .desc {
        max-width: 240px;
        font-size: 12px;
        text-align: left;
        color: #979ba5;
        line-height: 18px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .tag {
        position: relative;
        top: -5px;
        padding: 0 5px;
        border-radius: 2px;
        margin-left: 5px;
        background: #dcffe2;
        font-size: 12px;
        color: #2dcb56;
      }
      .count {
        color: #979BA5;
        font-size: 12px;
        padding: 0 5px;
        border-radius: 2px;
        background: #EAEBF0;
      }
    }
    .set-pf {
      padding-left: 20px;
    }
    .empty-wrapper {
      width: 100%;
      position: absolute;
      top: 208px;
      left: 50%;
      transform: translate(-50%, -50%);
      i {
        font-size: 48px;
        color: #c3cdd7;
      }
      :deep(.paas-table-serch .search-empty-tips) {
        white-space: nowrap !important;
      }
    }
    .line {
      height: 1px;
      background: #DCDEE5;
      margin: 6px 16px;
    }
  }
}
</style>

<style>
sysmark {
  font-weight: 700;
  color: #3a84ff;
  font-style: normal;
}
.system-input-cls .bk-input-text input {
  background: #f6f7fb;
}

.system-input-cls .bk-input-text input:focus {
  background: #f6f7fb !important;
}
</style>
