<template>
  <div class="detail-container pl10 pr10">
    <div class="title">
      {{ t('基本信息') }}
    </div>
    <bk-form ref="formRef" :model="formData" class="form-cls flex-row">
      <bk-form-item
        property="name"
        class="form-item-cls"
      >
        <template #label>
          <span class="label-cls">{{ t('名称：') }}</span>
        </template>
        <span class="value-cls">{{ formData.name }}</span>
      <!-- <bk-input
        v-model="formData.name"
        class="w700"
        :placeholder="t('由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于30个字符')"
        clearable
      /> -->
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('描述：') }}</span>
        </template>
        <span class="value-cls">{{ formData.description }}</span>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('标签：') }}</span>
        </template>
        <span class="value-cls">
          <bk-tag v-for="item in formData.labels" :key="item.id">{{ item.name }}</bk-tag>
        </span>
      </bk-form-item>
      <bk-form-item class="form-item-cls" :label="t('认证方式：')" :description="t('请求方需提供蓝鲸身份信息')">
        <span class="value-cls" v-if="formData.auth_config?.app_verified_required">
          {{ t('蓝鲸应用认证') }}，
        </span>
        <span class="value-cls" v-if="formData.auth_config?.auth_verified_required">
          {{ t('用户认证') }}
        </span>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('校验应用权限：') }}</span>
        </template>
        <span class="value-cls warning-c">
          {{ formData.auth_config?.resource_perm_required ? t('开启') : t('关闭') }}
        </span>
      </bk-form-item>
      <bk-form-item
        class="form-item-cls"
        :description="t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')"
        :label="t('是否公开：')">
        <span class="warning-c">{{ formData.is_public ? t('公开') : t('不公开') }}</span>
        <span class="value-cls" v-if="formData.is_public">
          {{ formData.allow_apply_permission ? t('（允许申请权限）') : t('（不允许申请权限）') }}
        </span>
      </bk-form-item>
      <!-- <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('已使用的环境:') }}</span>
        </template>
        <span>{{ formData.name }}</span>
      </bk-form-item> -->
    </bk-form>
    <div class="title">
      {{ t('前端配置') }}
    </div>
    <bk-form ref="formRef" :model="formData" class="form-cls flex-row">
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('请求方法：') }}</span>
        </template>
        <bk-tag :theme="methodsEnum[formData?.method]">{{ formData?.method }}</bk-tag>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('请求路径：') }}</span>
        </template>
        <span class="value-cls">{{ formData.path }}</span>
      </bk-form-item>
    </bk-form>
    <div class="title">
      {{ t('后端配置') }}
    </div>
    <bk-form ref="formRef" :model="formData" class="form-cls flex-row">
      <bk-form-item>
        <template #label>
          <span class="label-cls">{{ t('服务：') }}</span>
        </template>
        <span class="value-cls">{{ servicesData.name }}</span>
        <bk-table
          v-if="formData.id"
          class="table-layout w700"
          :data="servicesData.config"
          :border="['outer']"
        >
          <bk-table-column
            :label="t('环境名称')"
          >
            <template #default="{ data }">
              {{data?.stage?.name}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('后端服务地址')"
          >
            <template #default="{ data }">
              {{data?.hosts[0].scheme}}://{{ data?.hosts[0].host }}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('超时时间')"
            prop="timeout"
          >
          </bk-table-column>
        </bk-table>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('请求方法：') }}</span>
        </template>
        <bk-tag :theme="methodsEnum[formData.backend?.config?.method]">{{ formData.backend?.config?.method }}</bk-tag>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('请求路径：') }}</span>
        </template>
        <span class="value-cls">{{ formData.backend?.config?.path }}</span>
      </bk-form-item>
    </bk-form>
    <bk-button
      theme="primary"
      class="resource-btn-cls"
      @click="handleEditResource(formData.id)"
    >
      {{t('编辑')}}
    </bk-button>
    <bk-pop-confirm
      :title="t(`确认删除资源${formData?.name}？`)"
      content="删除操作无法撤回，请谨慎操作！"
      width="288"
      trigger="click"
      @confirm="handleDeleteResource(formData.id)"
    >
      <bk-button>
        {{ t('删除') }}
      </bk-button>
    </bk-pop-confirm>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { getResourceDetailData, getBackendsDetailData, deleteResources } from '@/http';
import { Message } from 'bkui-vue';
import { MethodsEnum } from '@/types';

const router = useRouter();

const props = defineProps({
  resourceId: {
    type: Number,
    default: 0,
  },
  apigwId: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(['done', 'deleted-success']);

const { t } = useI18n();

const formData = ref<any>({});

// 服务table
const servicesData = ref<any>({});

const methodsEnum: any = ref(MethodsEnum);

// 资源详情
const getResourceDetails = async () => {
  try {
    const res = await getResourceDetailData(props.apigwId, props.resourceId);
    formData.value = res;
    console.log('resourceDetail.value', formData.value);
    getServiceData();
  } catch (error) {

  }
};

// 选择服务获取服务详情数据
const getServiceData = async () => {
  const res = await getBackendsDetailData(props.apigwId, formData.value.backend.id);
  servicesData.value.config = res.configs;
  servicesData.value.name = res.name;
  emit('done', false);
};


// 编辑资源
const handleEditResource = (id: number) => {
  router.push({
    name: 'apigwResourceEdit',
    params: {
      resourceId: id,
    },
  });
};

// 删除资源
const handleDeleteResource = async (id: number) => {
  console.log('props.apigwId', props);
  await deleteResources(props.apigwId, id);
  Message({
    message: t('删除成功'),
    theme: 'success',
  });
  emit('deleted-success');
};

watch(
  () => props.resourceId,
  (v: number) => {
    if (v) {
      console.log('v', v);
      getResourceDetails();
    }
  },
  { immediate: true },
);

</script>
<style lang="scss" scoped>
.detail-container{
    max-width: 1000px;
    .title{
        color: #313238;
        font-weight: 700;
        font-size: 14px;
    }
    .form-cls{
      font-size: 12px;
      flex-flow: wrap;
      :deep(.form-item-cls){
        flex: 0 0 50%;
        margin-bottom: 5px;
        .bk-form-label{
          padding-right: 10px;
        }
      }
      .label-cls{
        font-size: 12px;
        color: #63656E;
      }
      .value-cls{
        color: #313238;
      }
    }
    .resource-btn-cls{
      margin-left: 150px;
    }
}
</style>
