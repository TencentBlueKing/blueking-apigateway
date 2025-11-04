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
  <div
    class="resource-top-bar"
    :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'"
  >
    <div class="top-title-wrapper">
      <div class="left">
        <div class="title">
          {{ t('资源配置') }}
        </div>
        <div
          v-show="showNewTips"
          class="is-latest"
        >
          {{ t('当前最新资源') }}
        </div>
        <div
          v-show="isDetail && currentSource?.name"
          class="current-resource flex items-center"
        >
          <AgIcon
            name="miaozhun"
            size="14"
            class="mr-4px mt-4px"
          />
          {{ currentSource?.name }}
        </div>
      </div>
      <div>
        <BkPopover
          ref="popoverRef"
          width="650"
          theme="light"
          trigger="click"
        >
          <div class="flex items-center cursor-pointer">
            <AiBluekingButton :tooltip-options="{ disabled: true }" />
            <div class="text-12px gradient-text-color">
              {{ t('资源文档一键翻译') }}
            </div>
          </div>
          <template #content>
            <div class="border-1px border-solid border-#fafbfd">
              <div>
                <div class="text-16px color-#313238 lh-24px mb-12px">
                  {{ t('资源文档一键翻译') }}
                </div>
                <div class="gradient-text-color mb-10px cursor-pointer">
                  {{ t('一键生成全部英文文档') }}
                </div>
              </div>
              <div>
                <AgTable
                  ref="tableRef"
                  :api-method="getTableData"
                  :columns="columns"
                  table-row-key="id"
                  resizable
                  select-on-row-click
                  @selection-change="handleResourceSelect"
                />
              </div>
              <div class="h-42px bg-#FAFBFD mx--12px mb--12px border-t-1px border-t-solid border-t-#DCDEE5;">
                <div class="flex items-center justify-end w-100% h-100% pr-14px">
                  <BkButton
                    class="h-26px"
                    theme="primary"
                    @click="handleTranslateConfirmClick"
                  >
                    {{ t('确定') }}
                  </BkButton>
                  <BkButton
                    class="h-26px ml-8px"
                    @click="handleCancelClick"
                  >
                    {{ t('取消') }}
                  </BkButton>
                </div>
              </div>
            </div>
          </template>
        </BkPopover>
      </div>
    </div>
  </div>
</template>

<script setup lang="tsx">
import AiBluekingButton from '@/components/ai-seek/AiBluekingButton.vue';
import { useStage } from '@/stores';
import AgTable from '@/components/ag-table/Index.vue';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import { getResourceList } from '@/services/source/resource.ts';
import { batchResourceDocAITranslate } from '@/services/source/ai.ts';
import AgIcon from '@/components/ag-icon/Index.vue';
import { Message } from 'bkui-vue';

interface IProps {
  latest?: boolean
  currentSource?: any
  isDetail?: boolean
  showNewTips?: boolean
  gatewayId: number
}

const {
  currentSource = {},
  isDetail = false,
  showNewTips = false,
  gatewayId,
} = defineProps<IProps>();

const { t } = useI18n();
const stage = useStage();

const selectedResources = ref<any[]>([]);
const tableRef = useTemplateRef('tableRef');
const popoverRef = useTemplateRef('popoverRef');

const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    colKey: 'row-select',
    type: 'multiple',
    align: 'center',
    fixed: 'left',
    width: 60,
    checkProps: ({ row }) => ({ disabled: !row.docs?.find(item => item.language === 'zh')?.id }),
  },
  {
    colKey: 'name',
    title: t('资源名称'),
  },
  {
    colKey: 'cn_doc',
    title: t('中文文档'),
    cell: (h, { row }) => <div>{getHasDocText(row, 'zh')}</div>,
  },
  {
    colKey: 'en_doc',
    title: t('英文文档'),
    cell: (h, { row }) => <div>{getHasDocText(row, 'en')}</div>,
  },
]);

const getTableData = async (params: Record<string, any> = {}) => getResourceList(toValue(gatewayId), params);

const getHasDocText = (resource: any, lang = 'zh') =>
  resource.docs?.find(item => item.language === lang)?.id ? t('有') : t('无');

const handleTranslateConfirmClick = async () => {
  await batchResourceDocAITranslate(toValue(gatewayId), {
    doc_ids: selectedResources.value.filter(item => item.docs?.find(doc => doc.language === 'zh')).map(item => item.docs.find(doc => doc.language === 'zh').id),
    target_language: 'en',
  });
  Message({
    theme: 'success',
    message: t('已启动翻译任务，请稍后查看翻译结果'),
  });
  tableRef.value!.refresh();
};

const handleResourceSelect = ({ selections }: { selections: any[] }) => {
  selectedResources.value = selections;
};

const handleCancelClick = () => {
  popoverRef.value?.hide();
};

</script>

<style lang="scss" scoped>
.resource-top-bar {
  position: absolute;
  display: flex;
  width: 100%;
  height: 52px;
  padding: 0 24px;
  background: #FFF;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;

  .top-title-wrapper {
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: space-between;

    .left {
      display: flex;
      align-items: center;

      .title {
        margin-right: 8px;
        font-size: 16px;
        color: #313238;
      }

      .is-latest {
        padding: 4px 8px;
        margin-right: 4px;
        font-size: 12px;
        color: #3A84FF;
        background: #EDF4FF;
        border-radius: 2px;
      }

      .current-resource {
        padding: 4px 8px;
        font-size: 12px;
        color: #4D4F56;
        background: #F0F1F5;
        border-radius: 2px;
      }
    }
  }
}

</style>

<style lang="scss">
.gradient-text-color {
  background-image: linear-gradient(#235DFA, #B881F0);
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
