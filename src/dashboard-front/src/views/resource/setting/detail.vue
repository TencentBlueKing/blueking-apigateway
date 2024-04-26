<template>
  <div class="detail-container pl10 pr10">
    <div class="title">
      {{ t('基本信息') }}
    </div>
    <bk-form ref="baseFormRef" :model="formData" :rules="rules" class="form-cls flex-row">
      <bk-form-item
        property="name"
        class="form-item-cls"
      >
        <template #label>
          <span class="label-cls">{{ t('名称：') }}</span>
        </template>

        <div v-if="!nameEdit" class="value-container">
          <span class="value-cls">{{ formData.name }}</span>
          <span class="operate-btn">
            <i @click="nameEdit = true" class="apigateway-icon icon-ag-edit-line"></i>
            <i class="apigateway-icon icon-ag-copy-info" @click="copy(formData.name)"></i>
          </span>
        </div>

        <div class="edit-name" v-else>
          <bk-input
            size="small"
            v-model="formData.name"
            @blur="handleEditSave"
            :placeholder="t('由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于30个字符')"
          />
        </div>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('描述：') }}</span>
        </template>

        <div v-if="!descEdit" class="value-container">
          <span class="value-cls">{{ formData.description }}</span>
          <span class="operate-btn">
            <i @click="descEdit = true" class="apigateway-icon icon-ag-edit-line"></i>
            <i class="apigateway-icon icon-ag-copy-info" @click="copy(formData.description)"></i>
          </span>
        </div>

        <div class="edit-name" v-else>
          <bk-input
            size="small"
            v-model="formData.description"
            @blur="handleEditSave"
            :placeholder="t('请输入描述')"
          />
        </div>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('标签：') }}</span>
        </template>

        <div v-if="!labelsEdit" class="value-container">
          <span class="value-cls">
            <bk-tag v-for="item in formData.labels" :key="item.id">{{ item.name }}</bk-tag>
          </span>
          <span class="operate-btn">
            <i @click="labelsEdit = true" class="apigateway-icon icon-ag-edit-line"></i>
            <i
              class="apigateway-icon icon-ag-copy-info"
              @click="copy(formData?.labels?.map(item => item.name)?.join(','))">
            </i>
          </span>
        </div>

        <div class="edit-name" v-else>
          <section style="width: 100%;">
            <SelectCheckBox
              :width="700"
              :cur-select-label-ids="formData.label_ids"
              :resource-id="resourceId"
              :labels-data="labelsData"
              @close="labelsEdit = false"
              @update-success="handleUpdateLabelSuccess"
              @label-add-success="initLabels"></SelectCheckBox>
          </section>
        </div>
      </bk-form-item>
      <bk-form-item class="form-item-cls" :label="t('认证方式：')" :description="t('请求方需提供蓝鲸身份信息')">
        <div v-if="!verifiedEdit" class="value-container">
          <span class="value-cls">
            {{ t(verifiedRequired(formData.auth_config)) }}
          </span>
          <span class="operate-btn">
            <i @click="verifiedEdit = true" class="apigateway-icon icon-ag-edit-line"></i>
            <i class="apigateway-icon icon-ag-copy-info" @click="copy(verifiedRequired(formData.auth_config))"></i>
          </span>
        </div>

        <div class="edit-name" v-else>
          <bk-popover
            disable-outside-click
            trigger="click"
            :is-show="verifiedEdit"
            :component-event-delay="300"
            :offset="16"
            placement="bottom"
            theme="light"
            width="490"
          >
            <span class="value-cls">
              {{ t(verifiedRequired(formData.auth_config)) }}
            </span>
            <template #content>
              <div style="padding: 4px;">
                <bk-form :model="formData" form-type="vertical">
                  <bk-form-item :label="t('认证方式')">
                    <bk-checkbox
                      v-model="formData.auth_config.app_verified_required_copy"
                      :disabled="!curApigwData.allow_update_gateway_auth">
                      <span class="bottom-line" v-bk-tooltips="{ content: t('请求方需提供蓝鲸应用身份信息') }">
                        {{ t('蓝鲸应用认证') }}
                      </span>
                    </bk-checkbox>
                    <bk-checkbox class="ml40" v-model="formData.auth_config.auth_verified_required_copy">
                      <span class="bottom-line" v-bk-tooltips="{ content: t('请求方需提供蓝鲸用户身份信息') }">
                        {{ t('用户认证') }}
                      </span>
                    </bk-checkbox>
                  </bk-form-item>
                  <bk-form-item :label="t('检验应用权限')" v-if="formData.auth_config.app_verified_required_copy">
                    <bk-switcher
                      v-model="formData.auth_config.resource_perm_required_copy"
                      :disabled="!curApigwData.allow_update_gateway_auth"
                      theme="primary"
                      size="small"
                    />
                  </bk-form-item>
                  <bk-form-item style="margin-bottom: 0;text-align: right;">
                    <bk-button
                      theme="primary"
                      native-type="button"
                      @click="verifiedSubmit"
                    >
                      确定
                    </bk-button>
                    <bk-button
                      style="margin-left: 8px;"
                      @click="verifiedEdit = false"
                    >
                      取消
                    </bk-button>
                  </bk-form-item>
                </bk-form>
              </div>
            </template>
          </bk-popover>
        </div>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('校验应用权限：') }}</span>
        </template>

        <div v-if="!permEdit" class="value-container">
          <span class="value-cls warning-c">
            {{ formData.auth_config?.resource_perm_required ? t('开启') : t('关闭') }}
          </span>
          <span class="operate-btn">
            <i @click="permEdit = true" class="apigateway-icon icon-ag-edit-line"></i>
            <i
              class="apigateway-icon icon-ag-copy-info"
              @click="copy(formData.auth_config?.resource_perm_required ? t('开启') : t('关闭'))">
            </i>
          </span>
        </div>

        <div class="edit-name" v-else>
          <bk-switcher
            v-model="formData.auth_config.resource_perm_required_copy"
            :disabled="!curApigwData.allow_update_gateway_auth"
            @change="verifiedSubmit"
            theme="primary"
            size="small"
            style="margin-top: 8px;"
          />
        </div>
      </bk-form-item>
      <bk-form-item
        class="form-item-cls"
        :description="t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')"
        :label="t('是否公开：')">
        <div v-if="!publicEdit" class="value-container">
          <span class="warning-c">{{ formData.is_public ? t('公开') : t('不公开') }}</span>
          <span class="value-cls" v-if="formData.is_public">
            {{ formData.allow_apply_permission ? t('（允许申请权限）') : t('（不允许申请权限）') }}
          </span>
          <span class="operate-btn">
            <i @click="publicEdit = true" class="apigateway-icon icon-ag-edit-line"></i>
          </span>
        </div>

        <div class="edit-name" v-else>
          <bk-switcher
            v-model="formData.is_public"
            @change="handleEditSave"
            theme="primary"
            size="small"
            style="margin-top: 8px;"
          />
        </div>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('已使用的环境：') }}</span>
        </template>
        <span v-if="!servicesData?.config?.length">--</span>
        <span v-else>{{ servicesData?.config?.map((item: any) => item?.stage?.name)?.join(', ') }}</span>
      </bk-form-item>
    </bk-form>

    <div class="title">{{ t('前端配置') }}</div>
    <bk-form ref="formRef" :model="formData" class="form-cls flex-row">
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('请求方法：') }}</span>
        </template>

        <div v-if="!frontMethodEdit" class="value-container">
          <bk-tag :theme="methodsEnum[formData?.method]">{{ formData?.method }}</bk-tag>
          <span class="operate-btn">
            <i @click="frontMethodEdit = true" class="apigateway-icon icon-ag-edit-line"></i>
          </span>
        </div>

        <div class="edit-name" v-else>
          <bk-select
            :input-search="false"
            :clearable="false"
            v-model="formData.method"
            @change="handleEditSave"
            class="method">
            <bk-option v-for="item in methodData" :key="item.id" :value="item.id" :label="item.name" />
          </bk-select>
        </div>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('请求路径：') }}</span>
        </template>

        <div v-if="!frontPathEdit" class="value-container">
          <span class="value-cls">{{ formData.path }}</span>
          <span class="operate-btn">
            <i @click="frontPathEdit = true" class="apigateway-icon icon-ag-edit-line"></i>
            <i class="apigateway-icon icon-ag-copy-info" @click="copy(formData.path)"></i>
          </span>
        </div>

        <div class="edit-name" v-else>
          <bk-popover
            disable-outside-click
            trigger="click"
            :is-show="frontPathEdit"
            :component-event-delay="300"
            :offset="16"
            placement="bottom"
            theme="light"
            width="490"
          >
            <span class="value-cls">{{ formData.path }}</span>
            <template #content>
              <div style="padding: 4px;">
                <bk-form :model="formData" form-type="vertical">
                  <bk-form-item :label="t('请求路径')" style="margin-bottom: 8px;">
                    <bk-input
                      v-model="formData.path_copy"
                      :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
                      style="margin-bottom: 12px;"
                    />
                    <bk-checkbox v-model="formData.match_subpath_copy" style="line-height: 20px;">
                      {{ t('匹配所有子路径') }}
                    </bk-checkbox>
                  </bk-form-item>
                  <bk-form-item style="margin-bottom: 0;text-align: right;">
                    <bk-button
                      theme="primary"
                      native-type="button"
                      @click="frontPathSubmit"
                    >
                      确定
                    </bk-button>
                    <bk-button
                      style="margin-left: 8px;"
                      @click="frontPathEdit = false"
                    >
                      取消
                    </bk-button>
                  </bk-form-item>
                </bk-form>
              </div>
            </template>
          </bk-popover>
        </div>
      </bk-form-item>
    </bk-form>

    <div class="title">{{ t('后端配置') }}</div>
    <bk-form ref="formRef" :model="formData" class="form-cls flex-row">
      <bk-form-item>
        <template #label>
          <span class="label-cls">{{ t('服务：') }}</span>
        </template>
        <span class="value-cls">{{ servicesData.name }}</span>
        <bk-table v-if="formData.id" class="table-layout" :data="servicesData.config" :border="['outer']">
          <bk-table-column :label="t('环境名称')" :resizable="false">
            <template #default="{ data }">
              {{data?.stage?.name}}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('后端服务地址')" :resizable="false">
            <template #default="{ data }">
              {{data?.hosts[0].scheme}}://{{ data?.hosts[0].host }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('超时时间')" prop="timeout" :resizable="false">
            <template #default="{ data }">
              {{ data?.timeout }}s
            </template>
          </bk-table-column>
        </bk-table>
      </bk-form-item>
      <bk-form-item class="form-item-cls">
        <template #label>
          <span class="label-cls">{{ t('请求方法：') }}</span>
        </template>

        <div v-if="!backMethodEdit" class="value-container">
          <bk-tag :theme="methodsEnum[formData.backend?.config?.method]">{{ formData.backend?.config?.method }}</bk-tag>
          <span class="operate-btn">
            <i @click="backMethodEdit = true" class="apigateway-icon icon-ag-edit-line"></i>
          </span>
        </div>

        <div class="edit-name" v-else>
          <bk-select
            :input-search="false"
            :clearable="false"
            v-model="formData.backend.config.method"
            @change="handleEditSave"
            class="method">
            <bk-option v-for="item in methodData" :key="item.id" :value="item.id" :label="item.name" />
          </bk-select>
        </div>
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
      :title="t('确认删除资源{resourceName}？', { resourceName: formData?.name || '' })"
      content="删除操作无法撤回，请谨慎操作！"
      width="288"
      trigger="click"
      @confirm="handleDeleteResource(formData.id)"
    >
      <bk-button class="resource-btn-cls" style="margin-left: 4px;">
        {{ t('删除') }}
      </bk-button>
    </bk-pop-confirm>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { getResourceDetailData, getBackendsDetailData, deleteResources, updateResources, getGatewayLabels } from '@/http';
import { Message } from 'bkui-vue';
import { copy } from '@/common/util';
import SelectCheckBox from './comps/select-check-box.vue';
import { MethodsEnum } from '@/types';
import { useCommon } from '@/store';

const { t } = useI18n();

const router = useRouter();
const common = useCommon();
const { curApigwData } = common;
const methodData = ref(common.methodList);

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

const rules = {
  name: [
    {
      required: true,
      message: t('请填写名称'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-zA-Z][a-zA-Z0-9_]{0,255}$|^$/;
        return reg.test(value);
      },
      message: '由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符',
      trigger: 'blur',
    },
  ],
};

const labelsData = ref([]);
const baseFormRef = ref();
const nameEdit = ref<boolean>(false);
const descEdit = ref<boolean>(false);
const labelsEdit = ref<boolean>(false);
const verifiedEdit = ref<boolean>(false);
const permEdit = ref<boolean>(false);
const publicEdit = ref<boolean>(false);
const frontMethodEdit = ref<boolean>(false);
const frontPathEdit = ref<boolean>(false);
const backMethodEdit = ref<boolean>(false);

const emit = defineEmits(['done', 'deleted-success']);

const formData = ref<any>({});

// 服务table
const servicesData = ref<any>({});

const methodsEnum: any = ref(MethodsEnum);

const initLabels = async () => {
  const res = await getGatewayLabels(common.apigwId);
  labelsData.value = res;
};
initLabels();

// 资源详情
const getResourceDetails = async () => {
  try {
    const res = await getResourceDetailData(props.apigwId, props.resourceId);
    formData.value = res;

    nextTick(() => {
      formData.value.label_ids = res?.labels?.map((item: any) => item.id);

      formData.value.auth_config.app_verified_required_copy = res?.auth_config?.app_verified_required;
      formData.value.auth_config.auth_verified_required_copy = res?.auth_config?.auth_verified_required;
      formData.value.auth_config.resource_perm_required_copy = res?.auth_config?.resource_perm_required;

      formData.value.path_copy = res?.path;
      formData.value.match_subpath_copy = res?.match_subpath;
      console.log('xxxxxxxxxxxxxxxxx', formData.value);
    });

    getServiceData();
  } catch (error) {

  }
};

// 更新成功
const handleUpdateLabelSuccess = () => {
  getResourceDetails();
  initLabels();
  labelsEdit.value = false;
};

// 选择服务获取服务详情数据
const getServiceData = async () => {
  const res = await getBackendsDetailData(props.apigwId, formData.value.backend.id);

  const resourceDetailTimeout = formData.value?.backend?.config?.timeout;
  if (resourceDetailTimeout !== 0) {
    res.configs.forEach((item: any) => {
      item.timeout = resourceDetailTimeout;
    });
  }
  servicesData.value.config = res.configs;
  servicesData.value.name = res.name;
  emit('done', false);
};

const verifiedRequired = (auth_config: any = {}) => {
  const { app_verified_required, auth_verified_required } = auth_config;
  if (app_verified_required && auth_verified_required) {
    return '蓝鲸应用认证， 用户认证';
  }
  if (app_verified_required) {
    return '蓝鲸应用认证';
  }
  if (auth_verified_required) {
    return '用户认证';
  }
  return '--';
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

// 修改资源
const handleEditSave = async () => {
  await baseFormRef.value?.validate();
  try {
    const params = { ...formData.value };
    await updateResources(props.apigwId, props.resourceId, params);
    Message({
      message: t('更新成功'),
      theme: 'success',
    });
    nameEdit.value = false;
    descEdit.value = false;
    labelsEdit.value = false;
    verifiedEdit.value = false;
    permEdit.value = false;
    publicEdit.value = false;
    frontMethodEdit.value = false;
    frontPathEdit.value = false;
    backMethodEdit.value = false;
  } catch (e) {
    console.error(e);
  };
};

// 认证方式修改
const verifiedSubmit = () => {
  formData.value.auth_config.app_verified_required = formData.value.auth_config.app_verified_required_copy;
  formData.value.auth_config.auth_verified_required = formData.value.auth_config.auth_verified_required_copy;
  formData.value.auth_config.resource_perm_required = formData.value.auth_config.resource_perm_required_copy;

  handleEditSave();
};

// 前端请求路径修改
const frontPathSubmit = () => {
  formData.value.path = formData.value.path_copy;
  formData.value.match_subpath = formData.value.match_subpath_copy;

  handleEditSave();
};

// 删除资源
const handleDeleteResource = async (id: number) => {
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
      getResourceDetails();
    }
  },
  { immediate: true },
);

</script>
<style lang="scss" scoped>
.detail-container{
    // max-width: 1000px;
    height: calc(100vh - 175px);
    overflow: auto;
    .title {
      color: #313238;
      font-weight: 700;
      font-size: 14px;
      margin-bottom: 18px;
    }
    .form-cls {
      font-size: 12px;
      flex-flow: wrap;
      :deep(.form-item-cls){
        flex: 0 0 50%;
        margin-bottom: 6px;
        .bk-form-label {
          font-size: 12px;
          padding-right: 10px;
          display: flex;
          justify-content: flex-end;
          .bk-form-label-description {
            border-bottom: none;
            position: relative;
            &::after {
              content: ' ';
              position: absolute;
              width: 82%;
              height: 1px;
              border-bottom: 1px dashed #979ba5;
              bottom: 4px;
              left: 0;
            }
          }
        }
      }
      .label-cls{
        font-size: 12px;
        color: #63656E;
      }
      .value-cls{
        color: #313238;
        cursor: pointer;
        .bk-tag {
          &:not(&:last-child) {
            margin-right: 4px;
          }
        }
      }
      .value-container {
        .operate-btn {
          display: none;
        }
      }
      .value-container:hover {
        .value-cls {
          color: #1768EF;
        }
        .operate-btn {
          display: inline-block;
        }
      }
    }
    .resource-btn-cls{
      margin-left: 150px;
      min-width: 88px;
      margin-top: 20px;
      &:last-child {
        margin-left: 4px;
      }
    }

    .apigateway-icon {
      cursor: pointer;
      color: #3A84FF;
      font-size: 14px;
      padding: 2px;
    }

    .edit-name {
      display: flex;
      align-items: center;
      .edit-name-icon {
        color: #3A84FF;
        margin-left: 4px;
        cursor: pointer;
        font-size: 16px;
        padding: 2px;
      }
    }
}
</style>
