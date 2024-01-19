<template>
  <div class="apigw-component-config-wrapper">
    <section class="item header">
      <div class="key"> {{ t('变量名') }} </div>
      <div class="value"> {{ t('变量值') }} </div>
    </section>
    <section
      v-for="(item, index) in configList"
      :key="index"
      :class="['item content', { 'no-border': !item.isShow }]">
      <div class="key" v-if="!!item.isShow">{{item.label}}</div>
      <div class="value">
        <bk-select
          style="margin-top: 8px;"
          v-if="item.type === 'enum'"
          v-model="item.default"
          filterable
          :input-search="false"
          @selected="handleSelected">
          <bk-option
            v-for="option in item.options"
            :key="option.id"
            :id="option.id"
            :name="option.name">
          </bk-option>
        </bk-select>
        <bk-input
          v-if="item.type === 'string' && !!item.isShow"
          v-model="item.default">
        </bk-input>
        <bk-input
          v-if="item.type === 'int' && !!item.isShow" v-model="item.default"
          type="number"
          :show-controls="false">
        </bk-input>
        <bk-input
          v-if="item.type === 'password' && !!item.isShow"
          type="password"
          v-model="item.default">
        </bk-input>
        <bk-checkbox
          v-if="item.type === 'boolean' && !!item.isShow"
          :true-value="true"
          :false-value="false"
          v-model="item.default">
        </bk-checkbox>
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import _ from 'lodash';
import { ref, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps({
  list: {
    type: Array,
    default: () => [],
  },
});

const configList = ref<any>([]);

const handleSelected = (value: any) => {
  configList.value?.forEach((item: any) => {
    if (item?.type !== 'enum' && item?.show_if) {
      const tempArr = item.show_if?.split('=');
      item.isShow = value === tempArr[1];
    }
  });
};

// const getData = () => {
//   const data = {};
//   configList.value?.forEach((item: any) => {
//     data[item.variable] = item.default;
//   });
//   return data;
// };

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
  () => props.list,
  (value) => {
    if (value?.length > 0) {
      const temps = _.cloneDeep(value);
      temps?.forEach((item: any) => {
        if (item?.type === 'enum') {
          const arrays: any = [];
          (item?.options || []).forEach((sub: any) => {
            arrays.push({
              id: sub[0],
              name: sub[1],
            });
          });
          item.options = _.cloneDeep(arrays);
          item.isShow = true;
        }
        if (item?.show_if) {
          const tempArr = item.show_if.split('=');
          const data: any = temps.find((sub: any) => sub.variable === tempArr[0]);
          item.isShow = data?.default === tempArr[1];
        } else {
          item.isShow = true;
        }
      });
      configList.value = temps;
    }
  },
  {
    immediate: true,
  },
);
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
