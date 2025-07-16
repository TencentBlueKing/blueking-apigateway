<template>
  <div class="body-payload">
    <div class="table-header">
      <div class="body-type">
        <div
          class="body-type-item"
          :class="[type === 'fromData' ? 'active' : '']"
          @click="() => handleTabChange('fromData')"
        >
          form-data
        </div>
        <div
          class="body-type-item"
          :class="[type === 'urlencoded' ? 'active' : '']"
          @click="() => handleTabChange('urlencoded')"
        >
          x-www-form-urlencoded
        </div>
        <div
          class="body-type-item"
          :class="[type === 'raw' ? 'active' : '']"
          @click="() =>handleTabChange('raw')"
        >
          raw
        </div>
        <BkSelect
          v-show="type === 'raw'"
          v-model="rawType"
          class="raw-select"
          :clearable="false"
          :filterable="false"
        >
          <BkOption
            v-for="(item, index) in datasource"
            :id="item.value"
            :key="index"
            :name="item.label"
            disabled
          />
        </BkSelect>
      </div>
      <!-- <div class="payload-type">
        <div class="payload-type-item active">
        <span class="icon apigateway-icon icon-ag-menu"></span>
        表格模式
        </div>
        <div class="payload-type-item">
        <span class="icon apigateway-icon icon-ag-menu"></span>
        代码模式
        </div>
        </div> -->
    </div>
    <EditTable
      v-show="type === 'fromData'"
      ref="dataRef"
      :list="fromDataList"
      @change="handleListChange"
    />
    <EditTable
      v-show="type === 'urlencoded'"
      ref="urlencodedRef"
      :list="urlencodedList"
      @change="handleListChange"
    />
    <div
      v-show="type === 'raw'"
      class="raw-content"
    >
      <EditorMonaco
        ref="resourceEditorRef"
        v-model="editorText"
        theme="Visual Studio"
        language="json"
        :minimap="false"
        show-format
        show-copy
        show-full-screen
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import EditTable from '@/views/online-debugging/components/EditTable.vue';
import EditorMonaco from '@/components/ag-editor/Index.vue';

interface IProps {
  fromDataPayload?: any[]
  rawPayload?: any
}

const {
  fromDataPayload = [],
  rawPayload = {},
} = defineProps<IProps>();

const emit = defineEmits<{ change: [data: any ] }>();

const type = ref<string>('raw');
const rawType = ref<string>('JSON');
const dataRef = ref();
const fromDataList = ref([]);
const urlencodedList = ref([]);
const urlencodedRef = ref();
const datasource = ref([
  {
    value: 'JSON',
    label: 'JSON',
  },
  {
    value: 'XML',
    label: 'XML',
  },
  {
    value: 'HTML',
    label: 'HTML',
  },
  {
    value: 'TEXT',
    label: 'TEXT',
  },
]);
const resourceEditorRef = ref<InstanceType<typeof EditorMonaco>>();
const editorText = ref(JSON.stringify(rawPayload, null, 2));

const validate = async () => {
  const formData = await dataRef.value?.validate();
  const urlencoded = await urlencodedRef.value?.validate();

  if (formData && urlencoded) {
    return true;
  }
  return false;
};

const getData = () => {
  return {
    type: type.value,
    formData: dataRef.value?.getTableData(),
    urlencoded: urlencodedRef.value?.getTableData(),
    raw: editorText.value,
    rawType: rawType.value,
  };
};

const handleListChange = (list) => {
  const data = {
    source: type.value,
    list,
  };
  emit('change', data);
};

const handleTabChange = (key: string) => {
  type.value = key;

  let list = [];
  if (key === 'fromData') {
    list = dataRef.value?.getTableData();
  }
  else if (key === 'urlencoded') {
    list = urlencodedRef.value?.getTableData();
  }
  list = list?.filter(item => item.name);

  handleListChange(list);
};

watch(
  () => fromDataPayload,
  (value) => {
    fromDataList.value = value;
  },
  { deep: true },
);

watch(
  () => rawPayload,
  (value) => {
    editorText.value = JSON.stringify(value, null, 2);
    resourceEditorRef.value?.setValue(editorText.value);
  },
  { deep: true },
);

defineExpose({
  validate,
  getData,
});
</script>

<style lang="scss" scoped>
.body-payload {
  height: 100%;
}
.table-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  .body-type {
    display: flex;
    align-items: center;
    padding-bottom: 10px;
    .body-type-item {
      padding: 4px 8px;
      background: #F0F1F5;
      border-radius: 11px;
      color: #63656E;
      font-size: 12px;
      cursor: pointer;
      &:not(:nth-last-child(1)) {
        margin-right: 8px;
      }
      &.active {
        color: #FFFFFF;
        background: #3A84FF;
        position: relative;
      }
    }
  }
}
.raw-select {
  width: 120px;
}
.raw-content {
  width: 100%;
  height: calc(100% - 50px);
  background: #FFFFFF;
  border: 1px solid #DCDEE5;
  border-radius: 2px;
}
</style>
