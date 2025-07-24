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
      <div class="system-list">
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
                  <span v-dompurify-html="highlight(item)" />
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
              v-dompurify-html="highlightDesc(item)"
              class="desc"
            />
          </div>
        </template>
        <template v-else>
          <div class="empty-wrapper">
            <TableEmpty
              :empty-type="tableEmptyConf.emptyType"
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
import { debounce } from 'lodash';
import { type ISystemItem } from '@/services/source/system';
import TableEmpty from '@/components/table-empty/Index.vue';

interface IProps { list?: ISystemItem[] }

interface Emits { (e: 'on-select', value?: ISystemItem): void }

const { list = [] } = defineProps<IProps>();
const emit = defineEmits<Emits>();

const { t } = useI18n();

const curList = ref([]);
const searchValue = ref('');
const curSelect = ref('*');
const isFilter = ref(false);
const tableEmptyConf = reactive({
  emptyType: '',
  isAbnormal: false,
});

const systemList = computed(() => list);
const allCount = computed(() => {
  return curList.value?.reduce((accumulator: number, current: ISystemItem) => {
    return accumulator + current.component_count;
  }, 0);
});

const updateTableEmptyConfig = () => {
  if (searchValue.value && !curList.value.length) {
    tableEmptyConf.emptyType = 'searchEmpty';
    return;
  }
  if (searchValue.value.length) {
    tableEmptyConf.emptyType = 'empty';
    return;
  }
  tableEmptyConf.emptyType = '';
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
  (value) => {
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
    min-width: 30px;
    height: 18px;
    background-color: #f0f1f5;
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
      background-color: #dcdee5;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-track {
      background-color: transparent;
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
          background-color: #a3c5fd;
          color: #ffffff;
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
          max-width: 182px;
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
        padding: 0 5px;
        border-radius: 2px;
        margin-left: 5px;
        background-color: #dcffe2;
        font-size: 12px;
        color: #2dcb56;
      }

      .count {
        color: #979ba5;
        font-size: 12px;
        padding: 0 5px;
        border-radius: 2px;
        background-color: #eaebf0;
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
      background-color: #dcdee5;
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
  background-color: #f6f7fb;
}

.system-input-cls .bk-input-text input:focus {
  background-color: #f6f7fb !important;
}
</style>
