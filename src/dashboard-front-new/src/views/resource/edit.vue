<template>
  <div class="edit-container">
    <bk-collapse
      class="collapse-cls p20"
      v-model="activeIndex"
      use-card-theme
    >
      <bk-collapse-panel name="baseInfo">
        <span class="panel-title">{{ t('基础信息') }}</span>
        <template #content>
          <div class="panel-content">
            <BaseInfo ref="baseInfoRef"></BaseInfo>
          </div>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="frontConfig">
        <span class="panel-title">{{ t('前端配置') }}</span>
        <template #content>
          <div class="panel-content">
            <FrontConfig ref="frontConfigRef"></FrontConfig>
          </div>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="backConfig">
        <span class="panel-title">{{ t('后端配置') }}</span>
        <template #content>
          <div class="panel-content">
            <BackConfig ref="backConfigRef"></BackConfig>
          </div>
        </template>
      </bk-collapse-panel>
    </bk-collapse>
    <div class="edit-footer">
      <bk-button
        theme="primary"
        class="ml20"
        @click="handleSubmit">
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
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseInfo from './comps/base-info.vue';
import FrontConfig from './comps/front-config.vue';
import BackConfig from './comps/back-config.vue';
import { useRouter } from 'vue-router';
const { t } = useI18n();
const router = useRouter();

// 默认展开
const activeIndex =  ref(['baseInfo', 'frontConfig', 'backConfig']);
const baseInfoRef = ref(null);
const frontConfigRef = ref(null);
const backConfigRef = ref(null);

// 提交
const handleSubmit = () => {
  const baseFormData = baseInfoRef.value.formData;
  const frontFormData = frontConfigRef.value.frontConfigData;
  const backFormData = backConfigRef.value.backConfigData;
  console.log('baseFormData', baseFormData.value, frontFormData.value, backFormData);
};

// 取消
const handleCancel = () => {
  router.back();
};

onMounted(() => {
  setTimeout(() => {
    console.log(11111, baseInfoRef.value.formData);
  }, 1000);
});
</script>
<style lang="scss" scoped>
  .edit-container{
    :deep(.collapse-cls){
      .bk-collapse-item{
        background: #fff;
        .panel-title{
            color: #63656e;
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
