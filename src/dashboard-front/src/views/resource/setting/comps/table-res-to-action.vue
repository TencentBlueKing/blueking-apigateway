<template>
  <bk-table
    :data="tableData"
    :pagination="pagination"
    row-key="name"
    show-overflow-tooltip
    v-bind="$attrs"
  >
    <bk-table-column
      :label="t('资源名称')"
      :min-width="160"
      fixed="left"
      prop="name"
      width="160"
    >
    </bk-table-column>
    <!--  认证方式列  -->
    <bk-table-column
      :label="() => renderAuthConfigColLabel()"
      :show-overflow-tooltip="false"
      width="100"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span v-bk-tooltips="{ content: `${getAuthConfigText(row?.auth_config)}`, placement: 'top' }">
          {{ getAuthConfigText(row?.auth_config) }}
        </span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('校验应用权限')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span
          :class="{ 'warning-c': getPermRequiredText(row?.auth_config) === '是' }"
        >{{ getPermRequiredText(row?.auth_config) }}</span>
      </template>
    </bk-table-column>
    <!--  “是否公开”列  -->
    <bk-table-column
      :label="() => renderIsPublicColLabel()"
      width="100"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span :class="{ 'warning-c': getPublicSettingText(row.is_public) === '是' }">
          {{ getPublicSettingText(row.is_public) }}
        </span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('允许申请权限')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span :class="{ 'warning-c': getAllowApplyPermissionText(row.allow_apply_permission) === '是' }">
          {{ getAllowApplyPermissionText(row.allow_apply_permission) }}
        </span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('前端请求路径')"
      :min-width="160"
      :width="160"
    >
      <template #default="{ row }">
        <span>{{ row.match_subpath ? row.path_display : row.path }}</span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('前端请求方法')"
      :show-overflow-tooltip="false"
      prop="method"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-tag :theme="methodsEnum[row.method]">{{ row.method }}</bk-tag>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('后端服务')"
      prop="method"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        {{ row.backend?.name ?? 'default' }}
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('后端请求方法')"
      :show-overflow-tooltip="false"
      prop="method"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-tag
          :theme="methodsEnum[row.backend?.config.method ?? row.method]"
        >
          {{ row.backend?.config.method ?? row.method }}
        </bk-tag>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('后端请求路径')"
      :min-width="160"
      :width="160"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        {{ row.backend?.config?.path ?? row.backend?.path ?? row.path }}
      </template>
    </bk-table-column>
    <bk-table-column
      :label="() => action === 'add' ? renderDocColLabel() : t('资源文档')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-button
          v-if="docConfig.showDoc"
          text
          theme="primary"
          @click="handleShowResourceDoc(row)"
        >
          <i class="apigateway-icon icon-ag-doc-2 mr4 f14 default-c" />
          {{ t('详情') }}
        </bk-button>
        <span v-else>{{ t('未生成') }}</span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('插件数量')"
      width="85"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-button
          style="font-size: 12px;"
          text theme="primary"
          @click="handleShowPluginsSlider(row)"
        >
          <span
            v-bk-tooltips="{ content: `${row.plugin_configs?.map((c)=>c.name || c.type).join('，') || '无插件'}` }"
          >
            {{ row.plugin_configs?.length ?? 0 }}
          </span>
        </bk-button>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('操作')"
      fixed="right"
      prop="act"
      width="150"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-button
          text
          theme="primary"
          @click="handleEdit(row)"
        >
          {{ t('修改配置') }}
        </bk-button>
        <bk-button
          class="pl10 pr10"
          text
          theme="primary"
          @click="() => {
            toggleRowUnchecked(row)
          }"
        >
          {{ t('不导入') }}
        </bk-button>
      </template>
    </bk-table-column>
    <template #empty>
      <TableEmpty
        :keyword="keyword"
        @clear-filter="handleClearFilter"
      />
    </template>
  </bk-table>
</template>

<script lang="tsx" setup>
import {
  ActionType,
  IAuthConfig,
  ILocalImportedResource,
  IPublicConfig,
} from '@/views/resource/setting/types';
import { ref, toRefs } from 'vue';
import { useI18n } from 'vue-i18n';
import { MethodsEnum } from '@/types';
import useTextGetter from '@/views/resource/setting/hooks/useTextGetter';
import TableEmpty from '@/components/table-empty.vue';
import { type IDocConfig } from '@/views/resource/setting/import.vue';

const {
  getAuthConfigText,
  getPermRequiredText,
  getPublicSettingText,
  getAllowApplyPermissionText,
} = useTextGetter();

const { t } = useI18n();
const methodsEnum = Object.freeze(MethodsEnum);

interface IProps {
  tableData: ILocalImportedResource[];
  action: ActionType;
  keyword: string;
  docConfig: IDocConfig;
}

const props = withDefaults(defineProps<IProps>(), {
  tableData: () => [],
  action: 'add',
  keyword: '',
  docConfig: () => ({
    showDoc: true,
    language: 'zh',
  }),
});

const emit = defineEmits<{
  'show-row-doc': [row: ILocalImportedResource]
  'show-row-plugin': [row: ILocalImportedResource]
  'show-row-edit': [row: ILocalImportedResource]
  'toggle-row-unchecked': [row: ILocalImportedResource]
  'confirm-auth-config': [action: ActionType]
  'confirm-pub-config': [action: ActionType]
  'confirm-doc-config': [docConfig: IDocConfig]
  'clear-filter': [action: ActionType]
}>();

const tempAuthConfig = defineModel<IAuthConfig>('tempAuthConfig', {
  required: true,
});

const tempPublicConfig = defineModel<IPublicConfig>('tempPublicConfig', {
  required: true,
});

const {
  tableData,
  action,
  keyword,
  docConfig,
} = toRefs(props);

const pagination = ref({
  count: tableData.value.length,
  limit: 10,
});

const localDocConfig = ref({ ...docConfig.value });

const handleShowResourceDoc = (row: ILocalImportedResource) => {
  emit('show-row-doc', row);
};

const handleShowPluginsSlider = (row: ILocalImportedResource) => {
  emit('show-row-plugin', row);
};

const handleEdit = (row: ILocalImportedResource) => {
  emit('show-row-edit', row);
};

const toggleRowUnchecked = (row: ILocalImportedResource) => {
  emit('toggle-row-unchecked', row);
};

// 批量修改认证方式确认后
const handleConfirmAuthConfig = () => {
  emit('confirm-auth-config', action.value);
};

// 批量修改认证方式取消后
const handleCancelAuthConfig = () => {
  tempAuthConfig.value = {
    app_verified_required: false,
    auth_verified_required: false,
    resource_perm_required: false,
  }
};

// 点击清空搜索条件后
const handleClearFilter = () => {
  emit('clear-filter', action.value);
};

// 批量修改公开设置确认后
const handleConfirmPublicConfig = () => {
  emit('confirm-pub-config', action.value);
};

// 批量修改公开设置取消后
const handleCancelPublicConfig = () => {
  tempPublicConfig.value = {
    is_public: false,
    allow_apply_permission: false,
  }
};

const handleConfirmDocConfig = () => {
  emit('confirm-doc-config', localDocConfig.value);
};

const renderAuthConfigColLabel = () => {
  return (
    <div>
      <div class="auth-config-col-label">
        <span>{t('认证方式')}</span>
        <bk-pop-confirm
          width="430"
          trigger="click"
          title={<span class="f16" style="color: #313238;">{t('批量修改认证方式')}</span>}
          content={
            <div class="multi-edit-popconfirm-wrap auth-config" style="margin-bottom: -12px;">
              <bk-form model={tempAuthConfig.value} labelWidth="110" labelPosition="right">
                <bk-form-item label={t('认证方式')} required={true} style="margin-bottom: 12px;">
                  <bk-checkbox
                    v-model={tempAuthConfig.value.app_verified_required}
                  >
                    <span class="bottom-line" v-bk-tooltips={{ content: t('请求方需提供蓝鲸应用身份信息') }}>
                    {t('蓝鲸应用认证')}
                    </span>
                  </bk-checkbox>
                  <bk-checkbox class="ml40" v-model={tempAuthConfig.value.auth_verified_required}>
                    <span class="bottom-line" v-bk-tooltips={{ content: t('请求方需提供蓝鲸用户身份信息') }}>
                    {t('用户认证')}
                    </span>
                  </bk-checkbox>
                </bk-form-item>
                {tempAuthConfig.value.app_verified_required ?
                  <bk-form-item
                    label={t('检验应用权限')}
                    description={t('蓝鲸应用需申请资源访问权限')}
                    style="margin-bottom: 12px;"
                  >
                    <bk-switcher
                      v-model={tempAuthConfig.value.resource_perm_required}
                      theme="primary"
                      size="small"
                    />
                  </bk-form-item> : ''
                }
              </bk-form>
            </div>
          }
          onConfirm={() => handleConfirmAuthConfig()}
          onCancel={() => handleCancelAuthConfig()}
        >
          <i
            class="apigateway-icon icon-ag-bulk-edit edit-action ml5 f14 default-c"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('批量修改认证方式')}
                </div>
              ),
            }}
          />
        </bk-pop-confirm>
      </div>
    </div>
  );
};

// 公开设置列 TSX
const renderIsPublicColLabel = () => {
  return (
    <div>
      <div class="public-config-col-label">
        <span>{t('是否公开')}</span>
        <bk-pop-confirm
          width="360"
          trigger="click"
          title={<span class="f16" style="color: #313238;">{t('批量修改公开设置')}</span>}
          content={
            <div class="multi-edit-popconfirm-wrap public-config" style="margin-bottom: -12px;">
              <bk-form model={tempPublicConfig.value} labelWidth="100" labelPosition="right">
                <bk-form-item
                  label={t('是否公开')}
                  required={true}
                  description={t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')}
                  style="margin-bottom: 12px;"
                >
                  <bk-switcher
                    v-model={tempPublicConfig.value.is_public}
                    theme="primary"
                    size="small"
                  />
                </bk-form-item>
                {tempPublicConfig.value.is_public ?
                  <bk-form-item style="margin-bottom: 12px;">
                    <bk-checkbox
                      v-model={tempPublicConfig.value.allow_apply_permission}
                    >
                      <span class="bottom-line">
                        {t('允许申请权限')}
                      </span>
                    </bk-checkbox>
                  </bk-form-item> : ''
                }
              </bk-form>
            </div>
          }
          onConfirm={() => handleConfirmPublicConfig()}
          onCancel={() => handleCancelPublicConfig()}
        >
          <i
            class="apigateway-icon icon-ag-bulk-edit edit-action ml5 f14 default-c"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('批量修改公开设置')}
                </div>
              ),
            }}
          />
        </bk-pop-confirm>
      </div>
    </div>
  );
};

// 是否生成文档列 TSX
const renderDocColLabel = () => {
  return (
    <div>
      <div class="public-config-col-label">
        <span>{t('资源文档')}</span>
        <bk-pop-confirm
          width="360"
          trigger="click"
          title={<span class="f16" style="color: #313238;">{t('批量修改资源文档')}</span>}
          content={
            <div class="multi-edit-popconfirm-wrap public-config" style="margin-bottom: -12px;">
              <bk-form model={localDocConfig.value} labelWidth="100" labelPosition="right">
                <bk-form-item
                  label={t('生成文档')}
                  style="margin-bottom: 12px;"
                >
                  <bk-switcher
                    v-model={localDocConfig.value.showDoc}
                    theme="primary"
                    size="small"
                  />
                </bk-form-item>
                {localDocConfig.value.showDoc ?
                 <bk-form-item
                   label={t('文档语言')}
                   style="margin-bottom: 12px;"
                 >
                   <bk-radio-group v-model={localDocConfig.value.language} size="small">
                     <bk-radio label="zh">{t('中文文档')}</bk-radio>
                     <bk-radio label="en">{t('英文文档')}</bk-radio>
                   </bk-radio-group>
                 </bk-form-item> : ''
                }
              </bk-form>
            </div>
          }
          onConfirm={() => handleConfirmDocConfig()}
        >
          <i
            class="apigateway-icon icon-ag-bulk-edit edit-action ml5 f14 default-c"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('批量修改资源文档')}
                </div>
              ),
            }}
          />
        </bk-pop-confirm>
      </div>
    </div>
  );
};
</script>

<style lang="scss" scoped>

</style>
