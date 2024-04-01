<template>
  <div class="edit-container">
    <bk-collapse
      class="page-wrapper-padding collapse-cls"
      v-model="activeIndex"
      use-card-theme
    >
      <bk-collapse-panel name="baseInfo">
        <template #header>
          <div class="panel-header">
            <angle-up-fill :class="[activeIndex?.includes('baseInfo') ? 'panel-header-show' : 'panel-header-hide']" />
            <div class="title">{{ t('基础信息') }}</div>
          </div>
        </template>
        <template #content>
          <BaseInfo ref="baseInfoRef" :detail="resourceDetail" :is-clone="isClone"></BaseInfo>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="frontConfig">
        <template #header>
          <div class="panel-header">
            <angle-up-fill
              :class="[activeIndex?.includes('frontConfig') ? 'panel-header-show' : 'panel-header-hide']"
            />
            <div class="title">{{ t('前端配置') }}</div>
          </div>
        </template>
        <template #content>
          <FrontConfig ref="frontConfigRef" :detail="resourceDetail" :is-clone="isClone"></FrontConfig>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="backConfig">
        <template #header>
          <div class="panel-header">
            <angle-up-fill :class="[activeIndex?.includes('backConfig') ? 'panel-header-show' : 'panel-header-hide']" />
            <div class="title">{{ t('后端配置') }}</div>
          </div>
        </template>
        <template #content>
          <BackConfig ref="backConfigRef" :detail="resourceDetail"></BackConfig>
        </template>
      </bk-collapse-panel>
    </bk-collapse>
    <div class="edit-footer">
      <bk-button
        theme="primary"
        style="width: 88px; margin-left: 25px;"
        @click="handleSubmit"
        :loading="submitLoading">
        {{ t('提交') }}
      </bk-button>
      <bk-button
        style="width: 88px; margin-left: 4px;"
        @click="handleCancel">
        {{ t('取消') }}
      </bk-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import mitt from '@/common/event-bus';
import { ref, computed, onMounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseInfo from './comps/base-info.vue';
import FrontConfig from './comps/front-config.vue';
import BackConfig from './comps/back-config.vue';
import { useRouter, useRoute } from 'vue-router';
import { useCommon } from '@/store';
import { createResources, getResourceDetailData, updateResources } from '@/http';
import { Message } from 'bkui-vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { useSidebar } from '@/hooks';

const { initSidebarFormData, isSidebarClosed } = useSidebar();
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
// 获取初始化表单数据做对比
const formDataBack = ref({});

const isClone = computed(() => {
  return route.name === 'apigwResourceClone';
});

const init = async () => {
  if (route.params.resourceId) {
    resourceId.value = route.params.resourceId;
    // 获取资源详情
    await getResourceDetails();
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
const handleCancel = async () => {
  const params = {
    baseFormData: baseInfoRef.value?.formData,
    frontFormData: frontConfigRef.value.frontConfigData,
    backFormData: backConfigRef.value.backConfigData,
  };
  const result = await isSidebarClosed(JSON.stringify(params));
  if (result) {
    router.back();
  }
};

onMounted(async () => {
  await init();
  formDataBack.value = {
    baseFormData: baseInfoRef.value?.formData,
    frontFormData: frontConfigRef.value?.frontConfigData,
    backFormData: backConfigRef.value?.backConfigData,
  };
  mitt.emit('on-leave-page-change', formDataBack.value);
  nextTick(() => {
    initSidebarFormData(formDataBack.value);
  });
});
</script>
<style lang="scss" scoped>
  .edit-container {
    :deep(.collapse-cls) {
      margin-bottom: 52px;
      .bk-collapse-item {
        background: #fff;
        box-shadow: 0 2px 4px 0 #1919290d;
        margin-bottom: 16px;
      }
    }
    .edit-footer {
      background: #fff;
      height: 52px;
      line-height: 52px;
      border: 1px solid #dcdee5;
      border-left: 0;
      position: fixed;
      bottom: 0;
      width: 100%;
      z-index: 2;
    }
    .panel-header {
      display: flex;
      align-items: center;
      padding: 24px;
      cursor: pointer;
      .title {
        font-weight: 700;
        font-size: 14px;
        color: #313238;
        margin-left: 8px;
      }
      .panel-header-show {
        transition: .2s;
        transform: rotate(0deg);
      }
      .panel-header-hide {
        transition: .2s;
        transform: rotate(-90deg);
      }
    }
    :deep(.bk-collapse-content) {
      padding-top: 0px !important;
      padding-left: 160px !important;
      .bk-input--text,
      .bk-select-tag-input {
        font-size: 14px;
        &::placeholder {
          font-size: 14px;
        }
      }
    }
  }
  .bk-collapse-demo {
    box-shadow: 0 0 8px 0px #ccc;
  }
</style>
