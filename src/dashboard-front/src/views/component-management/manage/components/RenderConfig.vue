/*
* TencentBlueKing is pleased to support the open source community by making
* 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
* Copyright (C) 2025 Tencent. All rights reserved.
* Licensed under the MIT License (the "License"); you may not use this file except
* in compliance with the License. You may obtain a copy of the License at
*
* http://opensource.org/licenses/MIT
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
  <div class="apigw-component-config-wrapper">
    <section class="item header">
      <div class="key">
        {{ t('变量名') }}
      </div>
      <div class="value">
        {{ t('变量值') }}
      </div>
    </section>
    <section
      v-for="(item, index) in configList"
      :key="index"
      class="item content"
      :class="[{ 'no-border': !item.isShow }]"
    >
      <div
        v-if="!!item.isShow"
        class="key"
      >
        {{ item.label }}
      </div>
      <div class="value">
        <BkSelect
          v-if="item.type === 'enum'"
          v-model="item.default"
          style="margin-top: 8px;"
          filterable
          :input-search="false"
          @selected="handleSelected"
        >
          <BkOption
            v-for="option in item.options"
            :id="option.id"
            :key="option.id"
            :name="option.name"
          />
        </BkSelect>
        <BkInput
          v-if="item.type === 'string' && !!item.isShow"
          v-model="item.default"
        />
        <BkInput
          v-if="item.type === 'int' && !!item.isShow"
          v-model="item.default"
          type="number"
          :show-controls="false"
        />
        <BkInput
          v-if="item.type === 'password' && !!item.isShow"
          v-model="item.default"
          type="password"
        />
        <BkCheckbox
          v-if="item.type === 'boolean' && !!item.isShow"
          v-model="item.default"
          true-value
          :false-value="false"
        />
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';

interface IProps { list?: any[] }

const { list = [] } = defineProps<IProps>();

const { t } = useI18n();

const configList = ref([]);

const handleSelected = (value: string) => {
  configList.value?.forEach((item: any) => {
    if (item?.type !== 'enum' && item?.show_if) {
      const tempArr = item.show_if?.split('=');
      item.isShow = value === tempArr[1];
    }
  });
};

const getData = () => {
  const data = {};
  configList.value?.forEach((item: any) => {
    data[item.variable] = item.default;
  });
  return data;
};

const setComponentConfig = () => {
  if (document.querySelectorAll('.value .bk-form-control')) {
    document.querySelectorAll('.value .bk-form-control')?.forEach((item: any) => {
      item.classList.add('inline-blocks');
    });
  }
};

onMounted(() => {
  setComponentConfig();
});

watch(
  () => list,
  (value) => {
    if (value?.length > 0) {
      const temps = cloneDeep(value);
      temps?.forEach((item: any) => {
        if (item?.type === 'enum') {
          const arrays: any = [];
          (item?.options || []).forEach((sub: any) => {
            arrays.push({
              id: sub[0],
              name: sub[1],
            });
          });
          item.options = cloneDeep(arrays);
          item.isShow = true;
        }
        if (item?.show_if) {
          const tempArr = item.show_if.split('=');
          const data: any = temps.find((sub: any) => sub.variable === tempArr[0]);
          item.isShow = data?.default === tempArr[1];
        }
        else {
          item.isShow = true;
        }
      });
      configList.value = temps;
    }
  },
  { immediate: true },
);

defineExpose({ getData });
</script>

<style lang="scss" scoped>
.apigw-component-config-wrapper {
  font-size: 14px;
  color: #63656e;

  .item {
    display: flex;
    justify-content: flex-start;

    .key {
      width: 180px;
    }

    .value {
      width: calc(100% - 180px);
    }

    .inline-blocks {
      display: inline-block !important;
    }

    &.no-border {
      border-bottom: none;
    }
  }

  .header {
    font-weight: bold;
    border-bottom: 1px solid #dcdee5;
  }

  .content {
    line-height: 48px;
    border-bottom: 1px solid #dcdee5;

    .value {
      display: flex;
      align-items: center;
    }
  }
}
</style>
