<template>
  <BkSideslider
    v-model:is-show="authSliderConfig.isShow"
    :title="authSliderConfig.title"
    :width="800"
    quick-close
    :before-close="handleBeforeClose"
    ext-cls="app-auth-slider"
    @hidden="handleCancel"
  >
    <template #default>
      <p class="ag-span-title">
        {{ t("你将对指定的蓝鲸应用添加访问资源的权限") }}
      </p>
      <BkForm
        class="m-b-30px m-l-15px"
        :label-width="120"
        :model="curAuthData"
      >
        <BkFormItem
          :label="t('蓝鲸应用ID')"
          required
        >
          <BkInput
            v-model="curAuthData.bk_app_code"
            class="code-input"
            :placeholder="t('请输入应用ID')"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('有效时间')"
          required
        >
          <BkRadioGroup v-model="curAuthData.expire_type">
            <BkRadio
              label="permanent"
              class="m-r-15px"
            >
              {{ t("永久有效") }}
            </BkRadio>
            <BkRadio label="custom">
              <BkInput
                v-model="curAuthData.expire_days"
                type="number"
                :min="0"
                class="w-85px m-r-5px"
                @focus="curAuthData.expire_type = 'custom'"
              />
              {{ t("天") }}
            </BkRadio>
          </BkRadioGroup>
        </BkFormItem>
      </BkForm>
      <p class="ag-span-title">
        {{ t("请选择要授权的资源") }}
      </p>
      <div class="m-l-20px">
        <BkRadioGroup
          v-model="curAuthData.dimension"
          class="ag-resource-radio"
        >
          <BkRadio label="api">
            {{ t("按网关") }}
            <span v-bk-tooltips="t('包括网关下所有资源，包括未来新创建的资源')">
              <i class="apigateway-icon icon-ag-help" />
            </span>
          </BkRadio>
          <BkRadio
            label="resource"
            class="m-l-0!"
          >
            {{ t("按资源") }}
            <span v-bk-tooltips="t('仅包含当前选择的资源')">
              <i class="apigateway-icon icon-ag-help" />
            </span>
          </BkRadio>
        </BkRadioGroup>
        <div
          v-if="['resource'].includes(curAuthData.dimension)"
          class="ag-transfer-box"
        >
          <BkTransfer
            :source-list="resourceTransferList"
            :display-key="'name'"
            :setting-key="'id'"
            :title="[t('未选资源'), t('已选资源')]"
            searchable
            @change="handleResourceChange"
          >
            <template #source-option="data">
              <div class="transfer-source-item">
                {{ data.name }}
              </div>
            </template>
            <template #target-option="data">
              <div class="transfer-source-item">
                {{ data.name }}
              </div>
            </template>
          </BkTransfer>
        </div>
      </div>
    </template>
    <template #footer>
      <BkButton
        class="w-88px"
        theme="primary"
        @click="handleSave"
      >
        {{ t("保存") }}
      </BkButton>
      <BkButton
        class="m-l-8px w-88px"
        @click="handleCancel"
      >
        {{ t("取消") }}
      </BkButton>
    </template>
  </BkSideslider>
</template>

<script lang="ts" setup>
import { cloneDeep, isEqual } from 'lodash-es';
import { t } from '@/locales';
import { usePopInfoBox } from '@/hooks';
import { type IResource } from '@/types/permission';

type ISliderParams = {
  isShow: boolean
  isLoading: boolean
  title: string
};

type IAuthData = {
  bk_app_code: string
  expire_type: string
  dimension: string
  expire_days: null | number
  resource_ids: string[] | number[]
};

interface IProps {
  sliderParams?: ISliderParams
  authData?: IAuthData
  resourceList?: IResource[]
}

interface Emits {
  (e: 'update:sliderParams', value: ISliderParams)
  (e: 'update:authData', value: IAuthData)
  (e: 'confirm'): void
}

const {
  sliderParams = {
    isShow: false,
    title: '',
  },
  authData = {
    bk_app_code: '',
    dimension: 'api',
    expire_type: 'permanent',
    expire_days: null,
    resource_ids: [],
  },
  resourceList = [],
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

const initData = ref({
  bk_app_code: '',
  expire_type: 'permanent',
  expire_days: null,
  resource_ids: [],
  dimension: 'api',
});

const authSliderConfig = computed({
  get: () => sliderParams,
  set: (params) => {
    emits('update:sliderParams', params);
  },
});

const curAuthData = computed({
  get: () => authData,
  set: (params) => {
    emits('update:authData', params);
  },
});

const resourceTransferList = computed(() => resourceList);

// 选择授权的资源数量发生改变触发
const handleResourceChange = (
  sourceList: IResource[],
  targetList: IResource[],
  targetValueList: number[],
) => {
  curAuthData.value.resource_ids = targetValueList;
};

const handleBeforeClose = () => {
  const isSame = isEqual(initData.value, curAuthData.value);
  if (!isSame) {
    usePopInfoBox({
      isShow: true,
      type: 'warning',
      title: t('确认离开当前页？'),
      subTitle: t('离开将会导致未保存信息丢失'),
      confirmText: t('离开'),
      cancelText: t('取消'),
      contentAlign: 'left',
      showContentBgColor: true,
      onConfirm() {
        authSliderConfig.value.isShow = false;
      },
      onClosed() {
        return false;
      },
    });
  }
  else {
    authSliderConfig.value.isShow = false;
  }
};

const handleSave = () => {
  emits('confirm');
};

const handleCancel = () => {
  authSliderConfig.value.isShow = false;
  curAuthData.value = cloneDeep(initData.value);
};
</script>

<style lang="scss" scoped>
.app-auth-slider {
  :deep(.bk-modal-content) {
    overflow-y: auto;
    padding: 30px;
    padding-bottom: 0;

    .bk-radio-label {
      font-size: 14px !important;
    }

    .code-input {
      width: 256px;
    }

    .ag-span-title {
      font-size: 14px;
      font-weight: bold;
      color: #63656e;
      margin-bottom: 20px;
    }

    .ag-resource-radio {
      display: block;

      label {
        display: block;
        margin-bottom: 10px;
      }
    }

    .ag-transfer-box {
      padding: 20px;
      background: #fafbfd;
      border: 1px solid #f0f1f5;
      border-radius: 2px;

      .bk-transfer {
        color: #63656e;

        :deep(.header) {
          font-weight: normal;
        }

        .transfer-source-item {
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }
      }
    }
  }

  :deep(.bk-sideslider-footer) {
    padding-left: 50px;
  }
}
</style>
