<template>
  <div class="edit-container">
    <bk-collapse
      class="collapse-cls p20"
      v-model="activeIndex"
      use-card-theme
    >
      <bk-collapse-panel name="baseInfo">
        <template #content>
          <div class="panel-title pt5 pb5">{{ t('基础信息') }}</div>
          <div class="panel-content">
            <BaseInfo ref="baseInfoRef" :detail="resourceDetail" :is-clone="isClone"></BaseInfo>
          </div>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="frontConfig">
        <template #content>
          <div class="panel-title pt5 pb5">{{ t('前端配置') }}</div>
          <div class="panel-content">
            <FrontConfig ref="frontConfigRef" :detail="resourceDetail" :is-clone="isClone"></FrontConfig>
          </div>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="backConfig">
        <template #content>
          <div class="panel-title pt5 pb5">{{ t('后端配置') }}</div>
          <div class="panel-content">
            <BackConfig ref="backConfigRef" :detail="resourceDetail"></BackConfig>
          </div>
        </template>
      </bk-collapse-panel>
    </bk-collapse>
    <div class="edit-footer">
      <bk-button
        theme="primary"
        class="ml20"
        @click="handleSubmit"
        :loading="submitLoading">
        {{ t('提交') }}
      </bk-button>
      <bk-button
        class="ml10"
        @click="handleCancel">
        {{ t('取消') }}
      </bk-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseInfo from './comps/base-info.vue';
import FrontConfig from './comps/front-config.vue';
import BackConfig from './comps/back-config.vue';
import { useRouter, useRoute } from 'vue-router';
import { useCommon } from '@/store';
import { createResources, getResourceDetailData, updateResources } from '@/http';
import { Message } from 'bkui-vue';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const common = useCommon();

const { apigwId } = common; // 网关id

// 默认展开
const activeIndex =  ref(['baseInfo', 'frontConfig', 'backConfig']);
const baseInfoRef = ref(null);
const frontConfigRef = ref(null);
const backConfigRef = ref(null);
const submitLoading = ref(false);
const resourceId = ref<any>(0);
const resourceDetail = ref<any>({});

const isClone = computed(() => {
  return route.name === 'apigwResourceClone';
});

const init = () => {
  if (route.params.resourceId) {
    resourceId.value = route.params.resourceId;
    // 获取资源详情
    getResourceDetails();
  }
};
const getResourceDetails = async () => {
  try {
    const res = await getResourceDetailData(apigwId, resourceId.value);
    resourceDetail.value = res;
  } catch (error) {

  }
};

// 提交
const handleSubmit = async () => {
  await baseInfoRef.value?.validate();
  await frontConfigRef.value?.validate();
  await backConfigRef.value?.validate();
  const baseFormData = baseInfoRef.value.formData;
  const frontFormData = frontConfigRef.value.frontConfigData;
  const backFormData = backConfigRef.value.backConfigData;
  try {
    submitLoading.value = true;
    const params = {
      ...baseFormData,
      ...frontFormData,
      backend: backFormData,
    };
    console.log('params', params);
    debugger;
    if (resourceId.value && !isClone.value) {
      await updateResources(apigwId, resourceId.value, params);
    } else {
      await createResources(apigwId, params);
    }
    Message({
      message: t(`${resourceId.value && !isClone.value ? '更新' : '新建'}成功`),
      theme: 'success',
    });
    router.push({
      name: 'apigwResource',
    });
  } catch (error) {
    console.log('error', error);
  } finally {
    submitLoading.value = false;
  }
};

// 取消
const handleCancel = () => {
  router.back();
};

init();
</script>
<style lang="scss" scoped>
  .edit-container{
    :deep(.collapse-cls){
      .bk-collapse-item{
        background: #fff;
        .bk-collapse-header{
          display: none;
        }
        .panel-title{
            color: #323339;
            font-weight: 700;
        }
        .panel-content{
            max-width: 1100px;
            width: 100%;
        }
      }
    }
    .edit-footer{
      background: #fff;
      height: 52px;
      line-height: 52px;
      border: 1px solid #DCDEE5;
    }
  }
    .bk-collapse-demo {
      box-shadow: 0 0 8px 0px #ccc;
    }
  </style>
