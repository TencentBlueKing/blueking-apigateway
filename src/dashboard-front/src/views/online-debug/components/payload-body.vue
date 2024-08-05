<template>
  <div class="body-payload">
    <div class="table-header">
      <div class="body-type">
        <div
          :class="['body-type-item', type === 'data' ? 'active' : '']"
          @click="type = 'data'">
          form-data
        </div>
        <div
          :class="['body-type-item', type === 'urlencoded' ? 'active' : '']"
          @click="type = 'urlencoded'">
          x-www-form-urlencoded
        </div>
        <div
          :class="['body-type-item', type === 'raw' ? 'active' : '']"
          @click="type = 'raw'">
          raw
        </div>
        <bk-select
          v-show="type === 'raw'"
          class="raw-select"
          v-model="rawType"
          :clearable="false"
          :filterable="false"
        >
          <bk-option
            v-for="(item, index) in datasource"
            :id="item.value"
            :key="index"
            :name="item.label"
            :disabled="true"
          />
        </bk-select>
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
    <edit-table v-show="type === 'data'" ref="dataRef" :list="fromDataList" />
    <edit-table v-show="type === 'urlencoded'" ref="urlencodedRef" :list="urlencodedList" />
    <div class="raw-content" v-show="type === 'raw'">
      <editor-monaco
        v-model="editorText"
        theme="Visual Studio"
        language="json"
        ref="resourceEditorRef"
        :minimap="false"
        :show-format="true"
        :show-copy="true"
        :show-full-screen="true"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
// import { useI18n } from 'vue-i18n';
import editTable from '@/views/online-debug/components/edit-table.vue';
import editorMonaco from '@/components/ag-editor.vue';

// const { t } = useI18n();

const props = defineProps({
  fromDataPayload: {
    type: Array,
    default: [],
  },
  rawPayload: {
    type: Object,
    default: {},
  },
});

const type = ref<string>('raw');
const rawType = ref<string>('JSON');
const dataRef = ref();
const fromDataList = ref<any[]>([]);
const urlencodedList = ref<any[]>([]);
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
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>();
const editorText = ref<any>(JSON.stringify(props.rawPayload, null, 2));

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

watch(
  () => props.fromDataPayload,
  (v: any) => {
    fromDataList.value = v;
  },
  {
    deep: true,
  },
);

watch(
  () => props.rawPayload,
  (v: any) => {
    editorText.value = JSON.stringify(v, null, 2);
    resourceEditorRef.value?.setValue(editorText.value);
  },
  {
    deep: true,
  },
);

defineExpose({
  validate,
  getData,
});
</script>

<style lang="scss" scoped>
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
        // padding-left: 36px;
        // &::before {
        //   position: absolute;
        //   content: ' ';
        //   width: 16px;
        //   height: 16px;
        //   border-radius: 50%;
        //   border: 1px solid #fff;
        //   top: 50%;
        //   transform: translateY(-50%);
        //   left: 12px;
        // }
        // &::after {
        //   position: absolute;
        //   content: ' ';
        //   width: 10px;
        //   height: 10px;
        //   border-radius: 50%;
        //   background: #FFFFFF;
        //   top: 50%;
        //   transform: translateY(-50%);
        //   left: 16px;
        // }
      }
    }
  }
}
.raw-select {
  width: 120px;
}
.raw-content {
  width: 100%;
  height: 312px;
  background: #FFFFFF;
  border: 1px solid #DCDEE5;
  border-radius: 2px;
}
</style>
