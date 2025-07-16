<template>
  <BkCollapse
    v-model="activeIndex"
    class="params-collapse"
  >
    <BkCollapsePanel :name="1">
      <template #header>
        <div class="params-header">
          <div class="params-header-title">
            <AgIcon
              name="angle-up-fill"
              class="params-header-fold"
              :class="[activeIndex?.includes(1) ? '' : 'fold']"
            />
            <span>{{ t('Headers 参数') }}</span>
          </div>
          <div
            class="presuppose-wrapper"
            @click="stopEvent"
          >
            <BkSelect
              v-model="presuppose"
              class="presuppose-select"
              :placeholder="t('预设')"
              :clearable="false"
              :filterable="false"
              :popover-min-width="238"
              @select="handleHeadersChange"
              @blur="handleBlur"
            >
              <BkOption
                v-for="(option, index) in localHeadersNames"
                :id="option.value"
                :key="option.value"
                :name="option.name"
              >
                <template #default>
                  <div
                    v-if="!option.isEdited"
                    class="select-option-row"
                    @mouseenter="() =>handleMouseEnter(index)"
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
                        style="margin-right: 3px;"
                        @click.stop="() => handleEditOptionItem(option)"
                      />
                      <BkPopConfirm
                        :title="t('确认删除该预设？')"
                        width="288"
                        trigger="click"
                        @confirm="() => handleDeleteOptionItemConfirm(option)"
                      >
                        <AgIcon
                          name="delet"
                          @click.stop="handleDeleteOptionItem"
                        />
                      </BkPopConfirm>
                    </div>
                  </div>
                  <div
                    v-else
                    style="width: 100%;"
                  >
                    <BkInput
                      ref="editInputRef"
                      :value="option.name"
                      :maxlength="20"
                      size="small"
                      :placeholder="t('请输入名称，enter保存')"
                      @click="(e: any) => stopEvent(e)"
                      @change="(v: string, e: any) => handlePresupposeChange(option, v, e)"
                      @blur="(e: any) => stopEvent(e)"
                      @enter="() => updateOption(option)"
                    />
                  </div>
                </template>
              </BkOption>
            </BkSelect>
            <BkButton
              theme="primary"
              text
              class="presuppose-btn"
              @click="setPresuppose"
            >
              {{ t('保存为预设') }}
            </BkButton>
          </div>
        </div>
      </template>
      <template #content>
        <div>
          <EditTable
            ref="editTableRef"
            :list="propsHeaders"
            type="headers"
            @change="handleChange"
          />
        </div>
      </template>
    </BkCollapsePanel>
  </BkCollapse>

  <BkDialog
    v-model:is-show="dialogData.isShow"
    :title="t('保存为预设 Header')"
    width="480px"
    quick-close
  >
    <div class="dialog-content">
      <div class="input-wrapper">
        <BkForm
          ref="formRef"
          form-type="vertical"
          :model="dialogData"
          :rules="rules"
        >
          <BkFormItem
            :label="t('名称')"
            property="name"
            required
            class="name"
          >
            <BkInput
              v-model="dialogData.name"
              :maxlength="20"
              :placeholder="t('请输入 20 个字符以内的名称')"
            />
          </BkFormItem>
        </BkForm>
      </div>

      <div class="header-list">
        <div class="tips">
          {{ t('保存后可通过预设名称直接渲染当前表格中的 Header') }}
        </div>
        <BkTable
          empty-cell-text="--"
          stripe
          :data="dialogData.table"
          :columns="dialogData.columns"
          show-overflow-tooltip
        />
      </div>
    </div>

    <template #footer>
      <BkButton
        theme="primary"
        :loading="dialogData.loading"
        @click="handleConfirm"
      >
        {{ t('确定') }}
      </BkButton>
      <BkButton
        class="ml8"
        @click="handleClosed"
      >
        {{ t('取消') }}
      </BkButton>
    </template>
  </BkDialog>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';
import { Message } from 'bkui-vue';
import headersValues from '@/constants/headers-value';
import EditTable from '@/views/online-debugging/components/EditTable.vue';

interface IProps { headersPayload?: any[] }

const { headersPayload = [] } = defineProps<IProps>();

const emit = defineEmits<{ change: [data: any ] }>();

const { t } = useI18n();

let local = localStorage.getItem('presupposeHeaders');
if (!local) {
  local = JSON.stringify([{
    name: 'Default JSON Header',
    id: String(+new Date()),
    list: [{
      isEdit: false,
      id: +new Date(),
      name: 'Content-Type',
      value: 'application/json',
      instructions: '',
      options: headersValues,
    }],
  }]);

  localStorage.setItem('presupposeHeaders', local);
}

const activeIndex = ref<number[]>([1]);
const editTableRef = ref();
const formRef = ref();
const propsHeaders = ref([]);
const newHeaders = ref([]);
const presuppose = ref('');
const hoverIndex = ref<number>();
const isIconClick = ref<boolean>(false); // 是否点击了icon
const editInputRef = ref(null);
const localHeaders = ref(JSON.parse(local) || []);
const dialogData = reactive({
  isShow: false,
  loading: false,
  name: '',
  table: [],
  columns: [
    {
      field: 'name',
      label: t('参数名'),
    },
    {
      field: 'value',
      label: t('参数值'),
    },
  ],
}); ;
const rules = {
  name: [{
    required: true,
    message: t('请输入名称'),
    trigger: 'blur',
  }],
};
const localHeadersNames = ref([]);

watch(
  () => localHeaders.value,
  (v) => {
    localHeadersNames.value = v?.map(item => ({
      name: item.name,
      value: item.id,
      isEdited: false,
    })) || [];
  },
  {
    deep: true,
    immediate: true,
  },
);

const stopEvent = (event: Event) => {
  event.stopPropagation();
  event.preventDefault();
};

const setPresuppose = () => {
  dialogData.table = newHeaders.value;
  dialogData.isShow = true;
};

const handleConfirm = async () => {
  try {
    await formRef.value?.validate();

    if (!newHeaders.value?.length) return;

    const current = [{
      name: dialogData.name,
      id: String(+new Date()),
      list: newHeaders.value,
    }];
    localHeaders.value = [...localHeaders.value, ...current];
    localStorage.setItem(
      'presupposeHeaders',
      JSON.stringify(localHeaders.value),
    );
    handleClosed();

    Message({
      message: t('保存成功'),
      theme: 'success',
    });
  }
  catch (err) {
    console.error(err);
    dialogData.loading = false;
  }
};

const handleMouseEnter = (index: number) => {
  hoverIndex.value = index;
};

const handleMouseLeave = () => {
  // 如果点击了icon 则不隐藏icon
  if (isIconClick.value) return;
  hoverIndex.value = null;
};

const handleDeleteOptionItem = () => {
  isIconClick.value = true;
};

const handleClosed = () => {
  dialogData.isShow = false;

  setTimeout(() => {
    dialogData.loading = false;
    dialogData.name = '';
    dialogData.table = [];
  }, 500);
};

const handlePresupposeChange = async (option, value: string, event: Event) => {
  stopEvent(event);
  if (!value) return;
  option.name = value;
  await updateOption(option);
};

const handleEditOptionItem = (option) => {
  localHeadersNames.value.forEach((item) => {
    item.isEdited = false;
  });
  option.isEdited = true;
  setTimeout(() => {
    editInputRef.value[0]?.focus();
  }, 500);
};

// 删除
const handleDeleteOptionItemConfirm = async (option) => {
  try {
    const { value } = option;

    localHeaders.value = localHeaders.value.filter(item => item.id !== value);
    localStorage.setItem(
      'presupposeHeaders',
      JSON.stringify(localHeaders.value),
    );

    if (presuppose.value === value) {
      presuppose.value = '';
    }

    Message({
      message: t('删除成功'),
      theme: 'success',
    });
  }
  catch (error) {
    console.error(error);
  }
};

const isUpdatingOption = ref(false);
// 更新
const updateOption = async (option) => {
  await new Promise(resolve => setTimeout(resolve, 100));
  if (isUpdatingOption.value) {
    return;
  }

  const { name, value } = option;
  try {
    if (name.trim()) {
      isUpdatingOption.value = true;

      const found = localHeaders.value.find(item => item.id === value);
      if (found) {
        found.name = name;
      }
      localStorage.setItem(
        'presupposeHeaders',
        JSON.stringify(localHeaders.value),
      );

      Message({
        message: t('修改成功'),
        theme: 'success',
      });

      localHeadersNames.value.forEach((item) => {
        item.isEdited = false;
      });
    }
  }
  catch (err) {
    console.error('修改失败', err);
  }
  finally {
    setTimeout(() => {
      isUpdatingOption.value = false;
    }, 200);
  }
};

// select 失焦时，移除所有 input 的编辑态
const handleBlur = () => {
  localHeadersNames.value.forEach((item) => {
    item.isEdited = false;
  });
};

const handleHeadersChange = () => {
  const found = localHeaders.value.find(item => item.id === presuppose.value);
  if (found) {
    const foundNames = found.list.map(item => item.name);
    const list = propsHeaders.value?.filter(item => !foundNames?.includes(item.name));
    propsHeaders.value = [...list, ...found.list];
  }
};

const validate = async () => {
  return await editTableRef.value?.validate();
};

const getData = () => {
  return editTableRef.value?.getTableData();
};

const handleChange = (list) => {
  newHeaders.value = list;
  emit('change', list);
};

watch(
  () => headersPayload,
  (value) => {
    propsHeaders.value = value;
    presuppose.value = '';
  },
  { deep: true },
);

defineExpose({
  validate,
  getData,
});

</script>

<style lang="scss" scoped>
.params-header {
  margin-bottom: 8px;
  cursor: pointer;
  .params-header-title {
    font-weight: 700;
    font-size: 14px;
    color: #313238;
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    .params-header-fold {
      margin-right: 8px;
      transition: all .2s;
      &.fold {
        transform: rotate(-90deg);
      }
    }
  }

  .presuppose-wrapper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    .presuppose-select {
      width: 80px;
    }
    .presuppose-btn {
      font-size: 14px;
      color: #3A84FF;
    }
  }
}
.params-collapse {
  :deep(.bk-collapse-content) {
    padding: 0;
  }
}
.dialog-content {
  .input-wrapper {
    margin-bottom: 12px;
    .name {
      font-size: 14px;
      color: #4D4F56;
    }
  }
  .header-list {
    padding-bottom: 18px;
    .tips {
      font-size: 14px;
      color: #979BA5;
      margin-bottom: 12px;
    }
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
</style>
