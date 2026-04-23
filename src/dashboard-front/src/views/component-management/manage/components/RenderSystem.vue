/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
<template>
  <div class="apigw-api-sys-filter">
    <div style="height: 100%">
      <section style="padding: 0 10px">
        <BkInput
          v-model="searchValue"
          ext-cls="system-input-cls"
          :placeholder="t('请输入系统名称、描述')"
          clearable
          right-icon="bk-icon icon-search"
          @input="handleSearch"
        />
      </section>
      <div
        class="system-list"
        :class="[
          { 'show-notice-wrapper': isShowNoticeAlert}
        ]"
      >
        <template v-if="curList.length > 0">
          <div
            class="item all-item"
            :class="[{ active: curSelect === '*' }]"
            @click="handleSelectAll"
          >
            <p class="flex items-center justify-between name all-wrapper">
              <span>
                <i class="m-r-4px apigateway-icon icon-ag-zonghe" />
                <span>{{ t("全部系统") }}</span>
              </span>
              <span class="all-count">
                <span class="count">{{ allCount }}</span>
              </span>
            </p>
          </div>
          <div class="line" />
          <div
            v-for="(item, index) in curList"
            :key="index"
            class="item set-pf"
            :class="[{ active: curSelect === item.id }]"
            @click="handleSelectSys(item)"
          >
            <div class="flex items-center justify-between m-b-4px name">
              <div class="flex items-center">
                <span class="title-wrapper">
                  <!-- eslint-disable-next-line vue/no-v-html -->
                  <span v-bk-xss-html="highlight(item)" />
                </span>
                <span
                  v-if="item.is_official"
                  class="tag"
                >
                  {{ t("官方") }}
                </span>
              </div>
              <div class="count">
                {{ item.component_count }}
              </div>
            </div>
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div
              v-bk-xss-html="highlightDesc(item)"
              class="desc"
            />
          </div>
        </template>
        <template v-else>
          <div class="empty-wrapper">
            <TableEmpty
              :empty-type="tableEmptyConf.emptyType"
              :abnormal="tableEmptyConf.isAbnormal"
              background="transparent"
              @clear-filter="clearFilterKey"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { debounce } from 'lodash-es';
import { useFeatureFlag } from '@/stores';
import { type ISystemItem } from '@/services/source/system';
import TableEmpty from '@/components/table-empty/Index.vue';

interface IProps { list?: ISystemItem[] }

interface Emits { (e: 'on-select', value?: ISystemItem): void }

const { list = [] } = defineProps<IProps>();
const emit = defineEmits<Emits>();

const { t } = useI18n();
const featureFlagStore = useFeatureFlag();

const curList = ref<ISystemItem[]>([]);
const searchValue = ref('');
const curSelect = ref<string | number>('*');
const isFilter = ref(false);
const tableEmptyConf = reactive<{
  emptyType: 'empty' | 'search-empty' | 'searchEmpty' | 'error' | undefined
  isAbnormal: boolean
}>({
  emptyType: undefined,
  isAbnormal: false,
});

const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);
const systemList = computed(() => list);
const allCount = computed(() => {
  return curList.value?.reduce((accumulator: number, current: ISystemItem) => {
    return accumulator + current.component_count;
  }, 0);
});

const updateTableEmptyConfig = () => {
  if (searchValue.value && !curList.value.length) {
    tableEmptyConf.emptyType = 'search-empty';
    return;
  }
  if (searchValue.value.length) {
    tableEmptyConf.emptyType = 'empty';
    return;
  }
  tableEmptyConf.emptyType = undefined;
};

const handleSearch = debounce((payload) => {
  if (!payload) {
    return;
  }
  isFilter.value = true;
  curList.value = systemList.value?.filter(({ name, description }: {
    name: string
    description: string
  }) => {
    const regex = new RegExp(`(${payload})`, 'gi');
    return !!name?.match(regex) || !!description?.match(regex);
  },
  );
  updateTableEmptyConfig();
});

const handleSelectSys = (payload: Partial<ISystemItem>) => {
  curSelect.value = payload?.id as any;
  emit('on-select', payload as ISystemItem);
};

const setSelected = (id: string | number) => {
  curSelect.value = id as any;
  emit('on-select', { id } as any);
};

const handleSelectAll = () => {
  curSelect.value = '*';
  emit('on-select', { id: '*' } as any);
};

const highlight = ({ name }: { name: string }) => {
  if (!name) {
    return '--';
  }
  const regex = new RegExp(`(${searchValue.value})`, 'gi');
  return name?.replace(regex, '<sysmark>$1</sysmark>');
};

const highlightDesc = ({ description }: { description: string }) => {
  if (!description) {
    return t('暂无描述');
  }
  if (description) {
    const regex = new RegExp(`(${searchValue.value})`, 'gi');
    return description?.replace(regex, '<sysmark>$1</sysmark>');
  }
  return t('暂无描述');
};

const clearFilterKey = () => {
  searchValue.value = '';
};

watch(
  () => systemList.value,
  (value: ISystemItem[]) => {
    curList.value = [...value];
  },
  { immediate: true },
);

watch(
  () => searchValue.value,
  (newVal, oldVal) => {
    if (!newVal && !!oldVal && isFilter.value) {
      isFilter.value = false;
      curList.value = [...systemList.value];
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
    display: inline-block;
    height: 18px;
    min-width: 30px;
    padding: 0 5px;
    font-size: 12px;
    line-height: 18px;
    color: #979ba5;
    text-align: center;
    background-color: #f0f1f5;
    border-radius: 2px;
  }

  .system-list {
    position: relative;
    height: calc(100% - 40px);
    margin-top: 6px;
    overflow-y: auto;

    &::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }

    &::-webkit-scrollbar-thumb {
      background-color: #dcdee5;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-track {
      background-color: transparent;
      border-radius: 3px;
    }

    .item {
      position: relative;
      height: 48px;
      padding: 4px 16px;
      overflow: hidden;
      text-align: left;
      cursor: pointer;

      &.all-item {
        padding: 0 16px;
      }

      &:hover {
        background-color: #e1ecff;

        .name {
          color: #3a84ff;
        }

        .all-wrapper {

          i {
            color: #3a84ff !important;
          }
        }

        .count {
          color: #fff;
          background-color: #a3c5fd;
        }
      }

      .name {
        max-width: 268px;
        overflow: hidden;
        font-size: 14px;
        color: #63656e;
        text-align: left;
        text-overflow: ellipsis;
        white-space: nowrap;

        .title-wrapper {
          display: inline-block;
          max-width: 182px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        &.all-wrapper {
          line-height: 48px;

          i {
            position: relative;
            top: -1px;
            color: #979ba5;
          }
        }
      }

      .desc {
        max-width: 240px;
        overflow: hidden;
        font-size: 12px;
        line-height: 18px;
        color: #979ba5;
        text-align: left;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .tag {
        padding: 0 5px;
        margin-left: 5px;
        font-size: 12px;
        color: #2dcb56;
        background-color: #dcffe2;
        border-radius: 2px;
      }

      .count {
        padding: 0 5px;
        font-size: 12px;
        color: #979ba5;
        background-color: #eaebf0;
        border-radius: 2px;
      }

      &.active {
        background-color: #e1ecff;

        .name {
          color: #3a84ff;
        }

        .all-wrapper i {
          color: #3a84ff !important;
        }
      }
    }

    .set-pf {
      padding-left: 20px;
    }

    .empty-wrapper {
      position: absolute;
      top: 208px;
      left: 50%;
      width: 100%;
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
      margin: 6px 16px;
      background-color: #dcdee5;
    }

    &.show-notice-wrapper {
      height: calc(100% - 80px);
    }
  }
}
</style>

<style>
/* stylelint-disable-next-line */
sysmark {
  font-style: normal;
  font-weight: 700;
  color: #3a84ff;
}

.system-input-cls .bk-input-text input {
  background-color: #f6f7fb;
}

.system-input-cls .bk-input-text input:focus {
  background-color: #f6f7fb !important;
}
</style>
