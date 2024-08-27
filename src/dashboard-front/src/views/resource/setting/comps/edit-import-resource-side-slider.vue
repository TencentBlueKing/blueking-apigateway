<template>
  <div class="edit-container">
    <bk-sideslider
      v-model:isShow="renderShow"
      width="960"
      title="修改配置"
      quick-close
      @hidden="handleHidden"
    >
      <template #default>
        <div class="collapse-wrap">
          <bk-collapse
            v-model="activeIndex"
            class="collapse-cls"
            use-card-theme
          >
            <bk-collapse-panel name="baseInfo">
              <template #header>
                <div class="panel-header">
                  <angle-up-fill
                    :class="[activeIndex?.includes('baseInfo') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">{{ t('基础信息') }}</div>
                </div>
              </template>
              <template #content>
                <base-info ref="baseInfoRef" :detail="props.resource"></base-info>
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
                <front-config ref="frontConfigRef" :detail="props.resource"></front-config>
              </template>
            </bk-collapse-panel>

            <bk-collapse-panel name="backConfig" :title="t('后端配置')">
              <template #header>
                <div class="panel-header">
                  <angle-up-fill
                    :class="[activeIndex?.includes('backConfig') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">{{ t('后端配置') }}</div>
                </div>
              </template>
              <template #content>
                <back-config ref="backConfigRef" :detail="props.resource"></back-config>
              </template>
            </bk-collapse-panel>
          </bk-collapse>
        </div>
      </template>
      <template #footer>
        <div>
          <bk-button
            theme="primary"
            @click="handleSubmit"
          >
            {{ t('保存') }}
          </bk-button>
          <bk-button style="margin-left: 8px;" @click="handleHidden"> {{ t('取消') }}</bk-button>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import BaseInfo from '@/views/resource/setting/comps/base-info.vue';
import FrontConfig from '@/views/resource/setting/comps/front-config.vue';
import BackConfig from '@/views/resource/setting/comps/back-config.vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { ILocalImportedResource } from '@/views/resource/setting/types';

const { t } = useI18n();

interface IProps {
  isSliderShow: boolean;
  resource: ILocalImportedResource | null;
}

const props = withDefaults(defineProps<IProps>(), {
  isSliderShow: false,
  resource: () => null,
});

const emits = defineEmits<{
  'on-hidden': [],
  submit: [resConfig: ILocalImportedResource]
}>();

// 默认展开
const activeIndex = ref(['baseInfo', 'frontConfig', 'backConfig']);
const baseInfoRef = ref(null);
const frontConfigRef = ref(null);
const backConfigRef = ref(null);
const renderShow = ref(props.isSliderShow);

// 提交
const handleSubmit = async () => {
  await Promise.all([
    baseInfoRef.value?.validate(),
    frontConfigRef.value?.validate(),
    backConfigRef.value?.validate(),
  ]);
  const baseFormData = baseInfoRef.value.formData;
  const frontFormData = frontConfigRef.value.frontConfigData;
  const backFormData = backConfigRef.value.backConfigData;
  try {
    const payload = {
      ...baseFormData,
      ...frontFormData,
      backend: { ...backFormData },
      _localId: props.resource._localId,
    };
    emits('submit', payload);
    emits('on-hidden');
  } catch (error) {
    console.log('error', error);
  }
};

const handleHidden = () => {
  renderShow.value = false;
  emits('on-hidden');
};

watch(() => props.isSliderShow, (val) => {
  renderShow.value = val;
});

</script>
<style scoped lang="scss">

:deep(.bk-modal-content) {
  background-color: #f5f7fa;
}

.collapse-wrap {
  padding: 24px 24px 0 24px;

  :deep(.collapse-cls) {
    margin-bottom: 24px;

    .bk-collapse-item {
      background: #fff;
      box-shadow: 0 2px 4px 0 #1919290d;
      margin-bottom: 16px;
    }
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
    padding-top: 0 !important;
    padding-left: 0 !important;
  }
}

:deep(.bk-modal-body),
:deep(.bk-sideslider-footer) {
  background-color: #f5f7fa;
}
</style>
