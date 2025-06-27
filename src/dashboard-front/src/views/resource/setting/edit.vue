<template>
  <div class="edit-container">
    <bk-collapse
      class="page-wrapper-padding collapse-cls"
      v-model="activeIndex"
      use-card-theme>
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
            <div class="title">{{ t('请求配置') }}</div>
          </div>
        </template>
        <template #content>
          <FrontConfig ref="frontConfigRef" :detail="resourceDetail" :is-clone="isClone"></FrontConfig>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="requestParams">
        <template #header>
          <div class="panel-header">
            <angle-up-fill
              :class="[activeIndex?.includes('requestParams') ? 'panel-header-show' : 'panel-header-hide']"
            />
            <div class="title">{{ t('请求参数') }}</div>
            <div class="sub-title">{{ t('非必填，可用于生成文档、在线调试、生成 MCP Server 等') }}</div>
          </div>
        </template>
        <template #content>
          <RequestParams
            ref="requestParamsRef"
            v-model:is-no-params="hasNoRequestParams"
            :detail="resourceDetail"
          />
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
          <BackConfig ref="backConfigRef" :detail="resourceDetail" @service-init="setupFormDataBack"></BackConfig>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="responseParams">
        <template #header>
          <div class="panel-header">
            <angle-up-fill
              :class="[activeIndex?.includes('responseParams') ? 'panel-header-show' : 'panel-header-hide']"
            />
            <div class="title">{{ t('响应参数') }}</div>
            <div class="sub-title">{{ t('非必填，可用于生成文档、在线调试、生成 MCP Server 等') }}</div>
          </div>
        </template>
        <template #content>
          <ResponseParams ref="responseParamsRef" :detail="resourceDetail" :is-clone="isClone" />
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
import {
  computed,
  nextTick,
  onMounted,
  ref,
} from 'vue';
import { useI18n } from 'vue-i18n';
import BaseInfo from './comps/base-info.vue';
import FrontConfig from './comps/front-config.vue';
import RequestParams from './comps/request-params.vue';
import BackConfig from './comps/back-config.vue';
import ResponseParams from './comps/response-params.vue';
import {
  useRoute,
  useRouter,
} from 'vue-router';
import { useCommon } from '@/store';
import {
  createResources,
  getResourceDetailData,
  updateResources,
} from '@/http';
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
const requestParamsRef = ref(null);
const backConfigRef = ref(null);
const responseParamsRef = ref(null);
const submitLoading = ref(false);
const resourceId = ref<any>(0);
const resourceDetail = ref<any>({});
// 获取初始化表单数据做对比
const formDataBack = ref({});
const hasNoRequestParams = ref(true);

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
  const res = await getResourceDetailData(apigwId, resourceId.value);
  if (res.schema?.none_schema) {
    hasNoRequestParams.value = true;
  } else if (res.schema?.parameters?.length || Object.keys(res.schema?.requestBody || {}).length) {
    hasNoRequestParams.value = false;
    // activeIndex.value.push('requestParams');
  }
  resourceDetail.value = res;
  mitt.emit('update-name', { name: res.name });
};

// 提交
const handleSubmit = async () => {
  try {
    // 校验表单数据
    await Promise.all([
      baseInfoRef.value?.validate(),
      frontConfigRef.value?.validate(),
      backConfigRef.value?.validate(),
    ]);
  } catch {
    // 校验失败，获取非法表单项的 #id
    const invalidFormElementIds = [
      ...baseInfoRef.value?.invalidFormElementIds,
      ...frontConfigRef.value?.invalidFormElementIds,
      ...backConfigRef.value?.invalidFormElementIds,
    ];
    if (invalidFormElementIds.length) {
      // 根据表单项 #id 获取元素，滚动到视图中间，并 focus
      const el = document.querySelector(`#${invalidFormElementIds[0]}`) as HTMLInputElement;
      if (el) {
        el.scrollIntoView({
          behavior: 'smooth', // 平滑滚动
          block: 'center',
        });
        el.focus?.();
      }
    }
    return;
  }

  const baseFormData = baseInfoRef.value.formData;
  const frontFormData = frontConfigRef.value.frontConfigData;
  const requestParamsData = hasNoRequestParams.value ? {} : requestParamsRef.value.getValue();
  const backFormData = backConfigRef.value.backConfigData;
  const responseParamsData = responseParamsRef.value.getValue();

  try {
    submitLoading.value = true;
    const params = {
      ...baseFormData,
      ...frontFormData,
      backend: backFormData,
      openapi_schema: {},
    };

    if (hasNoRequestParams.value) {
      params.openapi_schema.none_schema = true;
    } else {
      if (requestParamsData.parameters?.length) {
        params.openapi_schema.parameters = requestParamsData.parameters;
      }
      if (requestParamsData.requestBody) {
        params.openapi_schema.request_body = requestParamsData.requestBody;
      }
    }

    if (Object.keys(responseParamsData).length) {
      params.openapi_schema.responses = responseParamsData;
    }

    if (resourceId.value && !isClone.value) {
      Object.assign(params.openapi_schema, { version: resourceDetail.value.schema.version });
      await updateResources(apigwId, resourceId.value, params);
    } else {
      await createResources(apigwId, params);
    }

    formDataBack.value = {
      baseFormData: baseInfoRef.value.formData,
      frontFormData: frontConfigRef.value.frontConfigData,
      backFormData: backConfigRef.value.backConfigData,
    };

    mitt.emit('on-leave-page-change', formDataBack.value);
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

// 设置离开界面时检查是否有修改过表单时用的数据
// 页面加载完会默认执行一次，等 back-config 初始化数据之后会再执行一次，避免了错误判断表单是否已修改过的bug
const setupFormDataBack = () => {
  formDataBack.value = {
    baseFormData: baseInfoRef.value?.formData,
    frontFormData: frontConfigRef.value?.frontConfigData,
    backFormData: backConfigRef.value?.backConfigData,
  };

  nextTick(() => {
    mitt.emit('on-leave-page-change', formDataBack.value);
    initSidebarFormData(formDataBack.value);
  });
};

onMounted(async () => {
  await init();
  setupFormDataBack();
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

      .sub-title {
        margin-left: 12px;
        font-size: 14px;
        color: #979ba5;
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
      padding-top: 0 !important;
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
    box-shadow: 0 0 8px 0 #ccc;
  }
</style>
