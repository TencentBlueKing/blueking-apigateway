<template>
  <bk-select
    :style="{ maxWidth: `${width}px` }"
    class="select-wrapper mt5"
    :class="{ 'is-focus': _forceFocus }"
    filterable
    multiple
    multiple-mode="tag"
    ref="selectRef"
    :show-on-init="!isAdd"
    v-model="curLabelIds"
    selected-style="checkbox"
    :disable-focus-behavior="true"
    :popover-options="{
      extCls: 'select-check-box-popover-wrapper'
    }"
    @toggle="handleToggle"
    @blur="handleBlur"
  >
    <bk-option v-for="(option, index) in labelsData" :key="option.name" :id="option.id" :name="option.name">
      <template #default>
        <div
          v-bk-tooltips="{
            content: $t('标签最多只能选择10个'),
            disabled: !(!curLabelIds.includes(option.id) && curLabelIds.length >= 10) }"
          :disabled="!curLabelIds.includes(option.id) && curLabelIds.length >= 10"
          class="select-option-row"
          v-if="!option.isEdited"
          @mouseenter="handleMouseEnter(index)"
          @mouseleave="handleMouseLeave">
          <div class="select-option-row-name" :title="option.name">
            {{ option.name }}
          </div>
          <div class="icon-container" v-if="hoverIndex === index">
            <i
              class="icon apigateway-icon icon-ag-edit-line" style="margin-right: 3px;"
              @click.stop="handleEditOptionItem(option)"></i>
            <bk-pop-confirm
              title="确认删除该标签？"
              width="288"
              trigger="click"
              @confirm="handleDeleteOptionItemConfirm(option)">
              <i
                class="icon apigateway-icon icon-ag-delet"
                @click.stop="handleDeleteOptionItem"></i>
            </bk-pop-confirm>
          </div>
        </div>
        <div v-else style="width: 100%;">
          <bk-input
            ref="editInputRef"
            :value="option.name"
            size="small"
            @click="(e: any) => stopEvent(e)"
            @change="(v: string, e: any) => handleChange(option, v, e)"
            @blur="(e: any) => stopEvent(e)"
            @enter="updateOption(option)"
            :placeholder="t('请输入标签，enter保存')"
          />
        </div>
      </template>
    </bk-option>
    <template #extension>
      <div class="custom-extension" style="margin: 0 auto; width: 100%;">
        <div
          v-if="showEdit"
          class="flex-row align-items-center justify-content-center"
        >
          <bk-input
            style="width: 95%"
            ref="inputRef"
            v-model="optionName"
            size="small"
            @enter="addOption"
            :placeholder="t('请输入标签，enter保存')"
          />
        </div>
        <div v-else class="flex-row align-items-center justify-content-center" style="cursor: pointer; color: #63656e;">
          <div class="flex-row align-items-center justify-content-center" @click="handleShowEdit">
            <i class="apigateway-icon icon-ag-plus-circle plus-icon" />
            {{ t('新建标签') }}
          </div>
        </div>
      </div>
    </template>
  </bk-select>
</template>
<script setup lang="ts">
import { ref, computed, toRefs, PropType, watch, toValue } from 'vue';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
import { cloneDeep } from 'lodash';

import { updateResourcesLabels, createResourcesLabels, deleteResourcesLabels, updateResourcesLabelItem } from '@/http';

import { useCommon } from '@/store';

const emit = defineEmits(['close', 'update-success', 'label-add-success', 'update:modelValue']);
const common = useCommon();
const { t } = useI18n();
const { apigwId } = common; // 网关id

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  curSelectLabelIds: { type: Array, default: [] },   // 当前选中的label
  resourceId: { type: Number, default: 0 },
  labelsData: { type: Array as PropType<any>, default: [] },
  width: { type: Number, default: 235 },
  isAdd: { type: Boolean, default: false },
  // 是否强制让 select 进入 focus 态
  // 用于某些场景下 select 框不展示 focus 态样式的问题
  forceFocus: { type: Boolean, default: false },
});

const { curSelectLabelIds, resourceId, labelsData, width, isAdd, modelValue } = toRefs(props);

const curLabelIds = ref(curSelectLabelIds.value);
const showEdit = ref(false);
const optionName = ref('');
const inputRef = ref(null);
const selectRef = ref(null);
const editInputRef = ref(null);
const hoverIndex = ref<number>(null);
const isIconClick = ref<boolean>(false);  // 是否点击了icon
const _forceFocus = ref(toValue(props.forceFocus));

const curLabelIdsbackUp = ref(cloneDeep(curLabelIds.value));

// 相同的标签
const isSameLabels = computed(() => {
  const curLabelIdsString = JSON.stringify(curLabelIds.value.sort());
  const curLabelIdsbackUpString = JSON.stringify(curLabelIdsbackUp.value.sort());
  return curLabelIdsString === curLabelIdsbackUpString;
});

// 赋值给select curLabelIds
watch(modelValue, () => {
  if (modelValue.value.length) {
    curLabelIds.value = modelValue.value;
  }
});

watch(curLabelIds, () => {
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
  if (isAdd.value) return;
  setTimeout(async () => {
    // 关闭下拉框且
    if (!v) {
      // 变更了的标签数据请求接口
      if (!isSameLabels.value) {
        try {
          await updateResourcesLabels(apigwId, resourceId.value, { label_ids: curLabelIds.value });
          Message({
            message: t('修改标签成功'),
            theme: 'success',
            width: 'auto',
          });
          emit('update-success');
        } catch (error) {}
      } else {
        labelsData.value.forEach((item: any) => {
          item.isEdited = false;
        });
        emit('close');
      }
    }
  }, 500);
};

// 新增标签
const addOption = async () => {
  const optionNameTmp = optionName.value.trim();
  if (optionNameTmp) {
    const ret = await createResourcesLabels(apigwId, { name: optionNameTmp });
    Message({
      message: t('标签新建成功'),
      theme: 'success',
      width: 'auto',
    });
    optionName.value = '';
    if (curLabelIds.value.length < 10) {
      curLabelIds.value.push(ret.id);
      if (!isAdd.value) {
        await updateResourcesLabels(apigwId, resourceId.value, { label_ids: curLabelIds.value });
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

const isUpdatingOption = ref(false);
// 更新标签
const updateOption = async (option: any) => {
  await new Promise(resolve => setTimeout(resolve, 100));
  if (isUpdatingOption.value) {
    return;
  }

  const { name, id }: { name: string, id: number } = option;
  try {
    if (name.trim()) {
      isUpdatingOption.value = true;
      await updateResourcesLabelItem(apigwId, id, { name });
      Message({
        message: t('标签修改成功'),
        theme: 'success',
        width: 'auto',
      });
      labelsData.value.forEach((item: any) => {
        item.isEdited = false;
      });
      emit('update-success');
    }
  } catch (e) {
    console.error('标签修改失败', e);
  } finally {
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
  labelsData.value.forEach((item: any) => {
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
  try {
    await deleteResourcesLabels(apigwId, e.id);
    Message({
      message: t('删除标签成功'),
      theme: 'success',
      width: 'auto',
    });
    selectRef.value.showPopover();
    emit('update-success');
  } catch (error) {}
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
  labelsData.value.forEach((item: any) => {
    item.isEdited = false;
  });
};
</script>
<style scoped lang="scss">
.select-wrapper {
  :deep(.bk-select-tag-wrapper) {
    padding: 0;
  }
  :deep(.bk-select-tag) {
    padding-top: 4px;
    padding-bottom: 4px;
    .bk-tag {
      margin-right: 2px;
      margin-bottom: 0;
      margin-top: 0;
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
    .plus-icon {
      color: #979ba5;
      font-size: 14px;
      margin-right: 5px;
    }
  }

  .select-option-row {
    display: inline-block;
    width: 100%;
    position: relative;
    overflow: hidden;
    .icon-container {
      position: absolute;
      right: 0;
      top: 0;
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
