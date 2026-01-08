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
  <BkSelect
    ref="selectRef"
    v-model="curLabelIds"
    :style="{ maxWidth: `${width}px` }"
    class="select-wrapper"
    :class="{ 'is-focus': _forceFocus }"
    filterable
    multiple
    multiple-mode="tag"
    :show-on-init="!isAdd"
    selected-style="checkbox"
    disable-focus-behavior
    :popover-options="{
      extCls: 'select-check-box-popover-wrapper'
    }"
    @toggle="handleToggle"
    @blur="handleBlur"
  >
    <BkOption
      v-for="(option, index) in labelsData"
      :id="option.id"
      :key="option.name"
      :name="option.name"
    >
      <template #default>
        <div
          v-if="!option.isEdited"
          v-bk-tooltips="{
            content: t('标签最多只能选择10个'),
            disabled: !(!curLabelIds.includes(option.id) && curLabelIds.length >= 10) }"
          :disabled="!curLabelIds.includes(option.id) && curLabelIds.length >= 10"
          class="select-option-row"
          @mouseenter="() => handleMouseEnter(index)"
          @mouseleave="handleMouseLeave"
        >
          <div
            class="select-option-row-name"
            :title="option.name"
          >
            {{ option.name }}
          </div>
          <div
            v-if="hoverIndex === index"
            class="icon-container"
          >
            <AgIcon
              name="edit-line"
              class="icon mr-3px"
              @click.stop="() => handleEditOptionItem(option)"
            />
            <BkPopConfirm
              title="确认删除该标签？"
              width="288"
              trigger="click"
              @confirm="() => handleDeleteOptionItemConfirm(option)"
            >
              <AgIcon
                class="icon"
                name="delet"
                @click.stop="handleDeleteOptionItem"
              />
            </BkPopConfirm>
          </div>
        </div>
        <div
          v-else
          class="w-full"
        >
          <BkInput
            ref="editInputRef"
            :value="option.name"
            size="small"
            :placeholder="t('请输入标签，enter保存')"
            @click="(e: any) => stopEvent(e)"
            @change="(v: string, e: any) => handleChange(option, v, e)"
            @blur="(e: any) => stopEvent(e)"
            @enter="() => updateOption(option)"
          />
        </div>
      </template>
    </BkOption>
    <template #extension>
      <div class="custom-extension">
        <div
          v-if="showEdit"
          class="flex items-center justify-center"
        >
          <BkInput
            ref="inputRef"
            v-model="optionName"
            class="w-95%!"
            size="small"
            :placeholder="t('请输入标签，enter保存')"
            @enter="addOption"
          />
        </div>
        <div
          v-else
          class="flex items-center justify-center color-#63656e cursor-pointer"
        >
          <div
            class="flex items-center justify-center"
            @click="handleShowEdit"
          >
            <AgIcon
              name="plus-circle"
              class="plus-icon"
            />
            {{ t('新建标签') }}
          </div>
        </div>
      </div>
    </template>
  </BkSelect>
</template>

<script setup lang="ts">
import { Message } from 'bkui-vue';
import { updateResourceLabels } from '@/services/source/resource';
import {
  createLabels,
  deleteLabels,
  updateLabel,
} from '@/services/source/labels';
import { useRouteParams } from '@vueuse/router';

interface IProps {
  modelValue?: any[]
  curSelectLabelIds?: any[]
  resourceId?: number
  labelsData?: any[]
  width?: number
  isAdd?: boolean
  forceFocus?: boolean
  bathEdit?: boolean
}

const {
  modelValue = [],
  curSelectLabelIds = [],
  // 当前选中的label
  resourceId = 0,
  labelsData = [],
  width = 235,
  isAdd = false,
  // 用于某些场景下 select 框不展示 focus 态样式的问题
  forceFocus = false,
  // 批量编辑标签时，不需要更新某一资源的标签列表
  bathEdit = false,
} = defineProps<IProps>();

const emit = defineEmits<{
  'close': [data: any[]]
  'update-success': [void]
  'label-add-success': [id: number]
  'update:modelValue': [data: any[]]
}>();

const { t } = useI18n();
const gatewayId = useRouteParams('id', 0, { transform: Number });

const curLabelIds = ref([...curSelectLabelIds]);
const curLabelIdsbackUp = ref([...curLabelIds.value]);
const showEdit = ref(false);
const optionName = ref('');
const inputRef = ref();
const selectRef = ref();
const editInputRef = ref();
const hoverIndex = ref<number | null>(null);
const isIconClick = ref(false); // 是否点击了icon
const _forceFocus = ref(forceFocus);
const isUpdatingOption = ref(false);

// 相同的标签
const isSameLabels = computed(() => {
  const curLabelIdsString = JSON.stringify(curLabelIds.value.sort());
  const curLabelIdsbackUpString = JSON.stringify(curLabelIdsbackUp.value.sort());
  return curLabelIdsString === curLabelIdsbackUpString;
});

// 赋值给select curLabelIds
watch(
  () => modelValue,
  () => {
    if (modelValue.length) {
      curLabelIds.value = modelValue;
    }
  },
);

watch(
  () => curLabelIds.value, () => {
    emit('update:modelValue', curLabelIds.value || []);
  });

//
const handleToggle = async (v: boolean) => {
  if (!v) {
    showEdit.value = false;
    optionName.value = '';
    // 面板收起后去掉强制 focus 态
    _forceFocus.value = false;
  }
  // 新增标签标识
  if (isAdd || bathEdit) return;

  // 提前获取 gatewayId，避免组件收起后 gatewayId 被重置为默认值
  const _gatewayId = gatewayId.value;
  setTimeout(async () => {
    // 关闭下拉框且
    if (!v) {
      // 变更了的标签数据请求接口
      if (!isSameLabels.value) {
        await updateResourceLabels(_gatewayId, resourceId, { label_ids: curLabelIds.value });
        Message({
          message: t('修改标签成功'),
          theme: 'success',
          width: 'auto',
        });
        emit('update-success');
      }
      else {
        labelsData.forEach((item: any) => {
          item.isEdited = false;
        });
        // 把新的标签数据传递出去
        const newLabelData = labelsData.filter((label: any) => curLabelIds.value.includes(label.id));
        emit('close', newLabelData);
      }
    }
  }, 500);
};

// 新增标签
const addOption = async () => {
  const optionNameTmp = optionName.value.trim();
  if (optionNameTmp) {
    const ret = await createLabels(gatewayId.value, { name: optionNameTmp });
    Message({
      message: t('标签新建成功'),
      theme: 'success',
      width: 'auto',
    });
    optionName.value = '';
    if (curLabelIds.value.length < 10 && !bathEdit) {
      curLabelIds.value.push(ret.id);
      if (!isAdd) {
        await updateResourceLabels(gatewayId.value, resourceId, { label_ids: curLabelIds.value });
      }
    }
    emit('label-add-success', ret.id);
  }
  showEdit.value = false;
};

const handleChange = async (option: any, v: string, e: any) => {
  e.stopPropagation();
  e.preventDefault();
  option.name = v;
  await updateOption(option);
};

const stopEvent = (e: any) => {
  e.stopPropagation();
  e.preventDefault();
};

// 更新标签
const updateOption = async (option: any) => {
  await new Promise(resolve => setTimeout(resolve, 100));
  if (isUpdatingOption.value) {
    return;
  }

  const { name, id }: {
    name: string
    id: number
  } = option;
  try {
    if (name.trim()) {
      isUpdatingOption.value = true;
      await updateLabel(gatewayId.value, id, { name });
      Message({
        message: t('标签修改成功'),
        theme: 'success',
        width: 'auto',
      });
      labelsData.forEach((item: any) => {
        item.isEdited = false;
      });
      emit('update-success');
    }
  }
  catch (e) {
    console.error('标签修改失败', e);
  }
  finally {
    setTimeout(() => {
      isUpdatingOption.value = false;
    }, 200);
  }
};

// 展示新建标签input
const handleShowEdit = () => {
  showEdit.value = true;
  setTimeout(() => {
    inputRef.value.focus();
  });
};

const handleEditOptionItem = (e: any) => {
  labelsData.forEach((item: any) => {
    item.isEdited = false;
  });
  e.isEdited = true;
  setTimeout(() => {
    editInputRef.value[0]?.focus();
  }, 500);
};

// 点击了删除icon
const handleDeleteOptionItem = () => {
  isIconClick.value = true;
};

// 删除某个标签
const handleDeleteOptionItemConfirm = async (e: any) => {
  curLabelIds.value = curLabelIds.value.filter((item: number) => item !== e.id);
  await deleteLabels(gatewayId.value, e.id);
  Message({
    message: t('删除标签成功'),
    theme: 'success',
    width: 'auto',
  });
  selectRef.value.showPopover();
  emit('update-success');
};

// 输入框聚焦
// const handleInputFocus = () => {
//   nextTick(() => {
//     editInputRef.value[0].focus();
//   });
// };
// 鼠标移入事件
const handleMouseEnter = (i: number) => {
  hoverIndex.value = i;
};
// 处理鼠标移出
const handleMouseLeave = () => {
  // 如果点击了icon 则不隐藏icon
  if (isIconClick.value) return;
  hoverIndex.value = null;
};

// select 失焦时，移除所有 input 的编辑态
const handleBlur = () => {
  labelsData.forEach((item: any) => {
    item.isEdited = false;
  });
};
</script>

<style scoped lang="scss">
.select-wrapper {
  margin-top: 5px;

  :deep(.bk-select-tag-wrapper) {
    padding: 0;
  }

  :deep(.bk-select-tag) {
    padding-top: 4px;
    padding-bottom: 4px;

    .bk-tag {
      margin-top: 0;
      margin-right: 2px;
      margin-bottom: 0;
    }
  }
}

.select-check-box-popover-wrapper {
  // .item-container {
  //   width: 100%;
  //   position: relative;
  //   .icon-container {
  //     position: absolute;
  //     right: -20px;
  //     .icon {
  //       &:hover {
  //         color: #3a84ff;
  //       }
  //     }
  //   }
  // }

  &.bk-popover.bk-pop2-content.bk-select-popover {

    .bk-select-content-wrapper {

      .bk-select-option.is-multiple {
        padding-right: 10px;
      }
    }
  }

  .custom-extension {
    width: 100%;
    margin: 0 auto;

    .plus-icon {
      margin-right: 5px;
      font-size: 14px;
      color: #979ba5;
    }
  }

  .select-option-row {
    position: relative;
    display: inline-block;
    width: 100%;
    overflow: hidden;

    .icon-container {
      position: absolute;
      top: 0;
      right: 0;

      .icon {

        &:hover {
          color: #3a84ff;
        }
      }
    }

    .select-option-row-name {
      width: 74%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}
</style>
