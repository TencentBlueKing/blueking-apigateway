/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

<template>
  <div
    v-show="!importResult"
    class="import-wrapper"
  >
    <header class="steps-indicator-wrap">
      <main class="steps-indicator">
        <BkSteps
          :steps="[
            { title: t('校验文件') },
            { title: t('资源信息确认') },
          ]"
          :cur-step="curView === 'import' ? 1 : 2"
          theme="primary"
        />
      </main>
    </header>
    <ResourceImportEditor
      v-if="curView === 'import'"
      ref="importEditorRef"
      v-model="editorText"
      v-model:doc-config="docConfig"
      :is-code-valid="isCodeValid"
      :is-data-loading="isDataLoading"
      :validation-failure="validationFailure"
      @validate="() => validateEditor()"
    />
    <KeepAlive>
      <ResourceImportPreview
        v-if="curView === 'resources' && !importResult"
        :groups="previewGroups"
        :doc-config="docConfig"
        :is-ai-gateway="gatewayStore.isAIGateway"
        @toggle-resource="toggleRowUnchecked"
        @restore-all="handleRecoverAllRes"
        @edit-resource="handleEditSubmit"
        @update-auth-config="applyAuthConfig"
        @update-public-config="applyPublicConfig"
        @update-doc-config="docConfig = { ...$event }"
      />
    </KeepAlive>
    <footer class="page-actions-wrap">
      <main class="page-actions">
        <BkButton
          v-bk-tooltips="{
            content: isCodeModified ? t('请先进行语法检测') : t('请先修复报错信息后再导入'),
            disabled: isCodeValid && !isCodeModified,
          }"
          :theme="curView === 'import' ? 'primary' : ''"
          :loading="isDataLoading"
          :disabled="curView === 'import' && !isCodeValid"
          @click="handleStepClick"
        >
          {{ curView === 'import' ? t('下一步') : t('上一步') }}
        </BkButton>
        <span
          v-if="curView === 'resources'"
          v-bk-tooltips="{
            content: t('请确认导入的资源'),
            disabled: !resourcesToImport.length,
          }"
        >
          <BkButton
            theme="primary"
            type="button"
            :disabled="!resourcesToImport.length"
            :loading="importResult === 'loading'"
            @click="showImportConfirmDialog"
          >
            {{ t('确定导入') }}
          </BkButton>
        </span>
        <BkButton @click="goBack">
          {{ t('取消') }}
        </BkButton>
      </main>
    </footer>
    <!--  导入确认弹窗  -->
    <BkDialog
      v-model:is-show="isImportConfirmDialogVisible"
      class="custom-main-dialog"
      width="400"
      mask-close
    >
      <div class="dialog-content">
        <div class="dialog-title">
          {{ t('确认导入资源？') }}
        </div>
        <div class="dialog-main">
          <header class="mb-16px apigateway-name">
            {{ t('网关：') }}
            <span class="color-#313238 font-700">{{ getGatewayDisplayName(gatewayStore.currentGateway) }}</span>
            <span
              v-if="gatewayStore.currentGateway?.name"
              class="color-#63656e"
            >
              ({{ gatewayStore.currentGateway.name }})
            </span>
          </header>
          <main class="import-tips">
            {{ t('将新增') }}
            <span class="font-bold color-#34b97b">{{ previewGroups.add.length }}</span>
            {{ t('条资源，更新覆盖') }}
            <span class="font-bold color-#ffb400-c">{{ previewGroups.update.length }}</span>
            {{ t('条资源') }}
          </main>
        </div>
        <div class="dialog-footer">
          <BkButton
            theme="primary"
            @click="handleImportResource"
          >
            {{ t('确定导入') }}
          </BkButton>
          <BkButton
            class="ml-10px"
            @click="isImportConfirmDialogVisible = false"
          >
            {{ t('取消') }}
          </BkButton>
        </div>
      </div>
    </BkDialog>
  </div>
  <ResourceImportResult
    v-if="importResult"
    :status="importResult"
    :added-count="previewGroups.add.length"
    :updated-count="previewGroups.update.length"
    :error-message="importErrorMsg"
    @go-back="goBack"
    @retry="handleImportResource"
    @edit="importResult = null"
  />
</template>

<script setup lang="ts">
import { InfoBox, Message } from 'bkui-vue';
import { RESOURCE_IMPORT_EXAMPLE } from '@/constants';
import { checkResourceImport, importResource } from '@/services/source/gateway/resource';
import type { IResourceImportCheckInputSLZ } from '@/services/types/gateway/resource.ts';
import { useGateway } from '@/stores';
import type { ActionType, IAuthConfig, ILocalImportedResource, IPublicConfig, ResourceChangeType } from '@/types/resource';
import { getGatewayDisplayName } from '@/utils/gateway-name';
import { canAllowApplyPermission, normalizeAuthConfig } from '@/utils/auth-config';
import ResourceImportEditor from './components/ResourceImportEditor.vue';
import ResourceImportPreview from './components/ResourceImportPreview.vue';
import ResourceImportResult from './components/ResourceImportResult.vue';
import type { IImportDocConfig, IImportPreviewGroups, IImportValidationFailure, ImportResultStatus } from './types';

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const router = useRouter();
const gatewayStore = useGateway();

const editorText = ref(RESOURCE_IMPORT_EXAMPLE.content);
const importEditorRef = useTemplateRef<InstanceType<typeof ResourceImportEditor>>('importEditorRef');
const docConfig = ref<IImportDocConfig>({
  showDoc: true,
  language: 'zh',
});
const curView = ref<'import' | 'resources'>('import');
const isDataLoading = ref(false);
const validationStatus = ref<'dirty' | 'valid' | 'invalid'>('dirty');
const validationFailure = ref<IImportValidationFailure>();
const tableData = ref<ILocalImportedResource[]>([]);
// 变更类型只用于预览分组，不参与编辑或提交。
const resourceChangeTypes = ref<Record<number, ResourceChangeType>>({});
const isImportConfirmDialogVisible = ref(false);
const importResult = ref<ImportResultStatus | null>(null);
const importErrorMsg = ref('');
let checkRequestId = 0;

const isCodeValid = computed(() => validationStatus.value === 'valid');
const isCodeModified = computed(() => validationStatus.value === 'dirty');
const resourceDocParams = computed(() => docConfig.value.showDoc ? { doc_language: docConfig.value.language } : {});

const previewGroups = computed<IImportPreviewGroups>(() => {
  const groups: IImportPreviewGroups = {
    add: [],
    update: [],
    unchanged: [],
    excluded: [],
  };
  for (const row of tableData.value) {
    const change = resourceChangeTypes.value[row._localId];
    const group = change !== 'unchanged' && row._unchecked ? 'excluded' : change;
    groups[group].push(row);
  }
  return groups;
});

// 提交沿用预检返回顺序，与表格筛选条件无关。
const resourcesToImport = computed(() => tableData.value.filter(row =>
  !row._unchecked && resourceChangeTypes.value[row._localId] !== 'unchanged'));

watch(editorText, () => {
  validationStatus.value = 'dirty';
  validationFailure.value = undefined;
});

const handleStepClick = () => {
  if (curView.value === 'resources') {
    curView.value = 'import';
    return;
  }
  return validateEditor(true);
};

const validateEditor = async (showPreview = false) => {
  const snapshot = importEditorRef.value?.getSourceSnapshot();
  if (!snapshot?.content) {
    Message({
      theme: 'error',
      message: t('请输入Swagger内容'),
    });
    return;
  }

  const requestId = ++checkRequestId;
  const isCurrentRequest = () => requestId === checkRequestId && snapshot.isCurrent();

  try {
    isDataLoading.value = true;
    validationFailure.value = undefined;
    const params: IResourceImportCheckInputSLZ = {
      content: snapshot.content,
      allow_overwrite: true,
      ...resourceDocParams.value,
    };
    if (showPreview) {
      params.include_change_type = true;
    }

    const interceptorConfig = showPreview ? {} : { catchError: true };
    const resources = await checkResourceImport(gatewayId, params, interceptorConfig);
    if (!isCurrentRequest()) {
      return;
    }

    const changeTypes: Record<number, ResourceChangeType> = {};
    const rows = resources.map(({ change_type, ...resource }, index) => {
      changeTypes[index] = change_type ?? (resource.id === null ? 'add' : 'update');
      return {
        ...resource,
        _unchecked: false,
        _localId: index,
      };
    });
    resourceChangeTypes.value = changeTypes;
    tableData.value = rows;
    validationStatus.value = 'valid';
    if (showPreview) {
      curView.value = 'resources';
    }
  }
  catch (err: unknown) {
    if (isCurrentRequest()) {
      validationStatus.value = 'invalid';
      validationFailure.value = {
        content: snapshot.content,
        error: (err as { error?: IImportValidationFailure['error'] } | null)?.error,
      };
    }
  }
  finally {
    if (requestId === checkRequestId) {
      isDataLoading.value = false;
    }
  }
};

const showImportConfirmDialog = () => {
  if (!resourcesToImport.value.length) {
    return;
  }
  isImportConfirmDialogVisible.value = true;
};

// 确认导入
const handleImportResource = async () => {
  isImportConfirmDialogVisible.value = false;
  if (!resourcesToImport.value.length) {
    return;
  }
  try {
    importResult.value = 'loading';
    const importResources = resourcesToImport.value.map((resource: any) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { _unchecked, _localId, backend, ...resourceFields } = resource;
      return {
        ...resourceFields,
        backend_config: backend.config ? { ...backend.config } : null,
        backend_name: backend.name,
      };
    });
    await importResource(gatewayId, {
      import_resources: importResources,
      ...resourceDocParams.value,
    });
    importResult.value = 'success';
  }
  catch (err: unknown) {
    const error = err as { message: string };
    importErrorMsg.value = error?.message ? `${t('失败原因：')}${error.message}` : '';
    importResult.value = 'error';
  }
};

// 取消返回到资源列表
const goBack = () => {
  router.push({ name: 'ResourceSetting' });
};

const handleEditSubmit = (newResource: ILocalImportedResource) => {
  const index = tableData.value.findIndex(resource => resource._localId === newResource._localId);
  if (index !== -1) {
    tableData.value[index] = {
      ...tableData.value[index],
      ...newResource,
    };
  }
};

// 切换资源是否导入
const toggleRowUnchecked = (row: ILocalImportedResource) => {
  if (resourceChangeTypes.value[row._localId] === 'unchanged') {
    return;
  }
  const data = tableData.value.find(resource => resource._localId === row._localId);
  if (data) {
    data._unchecked = !data._unchecked;
  }
};

// 还原所有不导入的资源
const handleRecoverAllRes = () => {
  previewGroups.value.excluded.forEach(data => data._unchecked = false);
};

const applyAuthConfig = (action: ActionType, config: IAuthConfig) => {
  const authConfig = normalizeAuthConfig(config);
  const lockV1AppAuth = !gatewayStore.isResourceAuthV2 && !gatewayStore.currentGateway?.allow_update_gateway_auth;
  previewGroups.value[action].forEach((row) => {
    const existingAuth = normalizeAuthConfig(row.auth_config);
    // V1 批量表单没有公开客户端选项；当网关禁止修改应用认证时，应用认证与权限校验同样处于锁定态，均保留各资源原值。
    const nextAuth: IAuthConfig = {
      ...authConfig,
      ...(lockV1AppAuth
        ? {
          app_verified_required: existingAuth.app_verified_required,
          resource_perm_required: existingAuth.resource_perm_required,
        }
        : {}),
      oauth2_public_client_enabled: gatewayStore.isResourceAuthV2
        ? authConfig.oauth2_public_client_enabled
        : authConfig.auth_verified_required && existingAuth.oauth2_public_client_enabled,
    };
    row.auth_config = nextAuth;
    if (!canAllowApplyPermission(Boolean(row.is_public), nextAuth)) {
      row.allow_apply_permission = false;
    }
  });
};

const applyPublicConfig = (action: ActionType, config: IPublicConfig) => {
  previewGroups.value[action].forEach((row) => {
    row.is_public = config.is_public;
    row.allow_apply_permission = config.allow_apply_permission
      && canAllowApplyPermission(config.is_public, row.auth_config);
  });
};

// 监听路由离开，提示用户是否要在导入中离开
onBeforeRouteLeave((to, from, next) => {
  // 如果正在导入中...
  if (importResult.value === 'loading') {
    InfoBox({
      title: t('确认离开当前页？'),
      subTitle: t('离开将会导致未保存信息丢失'),
      confirmText: t('离开'),
      cancelText: t('取消'),
      onConfirm() {
        next();
      },
      onClose() {
        return false;
      },
    });
  }
  else next();
});
</script>

<style scoped lang="scss">
.import-wrapper {
  position: relative;
  min-height: 100%;

  .steps-indicator-wrap,
  .page-actions-wrap {
    z-index: 100;
    display: flex;
    height: 52px;
    background: #FFF;
    align-items: center;
  }

  .steps-indicator-wrap {
    position: sticky;
    top: 0;
    justify-content: center;
    border-bottom: 1px solid #DCDEE5;

    .steps-indicator {
      width: 360px;
    }
  }

  .page-actions-wrap {
    position: sticky;
    right: 0;
    bottom: 0;
    left: 0;
    padding-left: 48px;
    border-top: 1px solid #DCDEE5;

    .page-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}

.custom-main-dialog {

  :deep(.bk-dialog-title) {
    display: none;
  }

  :deep(.bk-modal-footer) {
    display: none;
  }

  .dialog-content {

    .publish-icon {
      margin-bottom: 18px;
      font-size: 42px;
      line-height: 32px;
      text-align: center;
    }

    .dialog-title {
      margin-bottom: 16px;
      font-size: 20px;
      color: #313238;
      text-align: center;
    }

    .dialog-main {

      .import-tips {
        padding: 12px 16px;
        margin-bottom: 25px;
        color: #63656E;
        background: #F5F6FA;
        border-radius: 2px;

        span {
          font-weight: 700;
        }
      }
    }

    .dialog-footer {
      text-align: center;
    }
  }
}
</style>
