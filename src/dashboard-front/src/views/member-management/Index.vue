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
  <div class="page-wrapper-padding member-management-page">
    <div class="member-toolbar">
      <div class="toolbar-left">
        <BkButton
          theme="primary"
          :disabled="loading"
          @click="handleAdd"
        >
          {{ t('新增成员') }}
        </BkButton>
        <BkRadioGroup v-model="activeRole">
          <BkRadioButton
            v-for="tab in roleTabs"
            :key="tab.key"
            :label="tab.key"
          >
            {{ tab.label }} ({{ tab.count }})
          </BkRadioButton>
        </BkRadioGroup>
        <BkButton
          text
          theme="primary"
          @click="handleViewPermissionModel"
        >
          {{ t('查看权限模型') }}
        </BkButton>
      </div>
      <BkInput
        v-model="keyword"
        class="search-input"
        clearable
        :placeholder="t('搜索用户名')"
        :right-icon="'bk-icon icon-search'"
      />
    </div>

    <BkLoading :loading="loading">
      <AgTable
        v-model:table-data="displayMembers"
        local-page
        table-row-key="id"
        :show-settings="false"
        :max-limit-config="{ allocatedHeight: 220, mode: 'tdesign' }"
        :columns="columns"
        :table-empty-type="keyword ? 'search-empty' : 'empty'"
        @clear-filter="keyword = ''"
      />
    </BkLoading>

    <AddMember
      v-model:is-show="isAddShow"
      @done="handleMembersChanged"
    />
    <EditMember
      v-model:is-show="isChangeShow"
      :admin-count="adminCount"
      :member="changeMember"
      @done="handleMembersChanged"
    />
    <CheckPermissionModel
      v-model:is-show="isModelShow"
    />
  </div>
</template>

<script setup lang="tsx">
import { Message } from 'bkui-vue';
import { usePopInfoBox } from '@/hooks';
import {
  deleteGatewayMember,
  getGatewayMemberList,
} from '@/services/source/gateway-member';
import { useFeatureFlag, useGateway, useUserInfo } from '@/stores';
import AgTable from '@/components/ag-table/Index.vue';
import type { PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
import AddMember from './components/AddMember.vue';
import EditMember from './components/EditMember.vue';
import CheckPermissionModel from './components/CheckPermissionModel.vue';
import type { IMember } from './types';
import {
  getRoleDescription,
  getRoleLabel,
} from './utils';
import type { MemberRole } from '@/constants/gateway-permission';

type RoleTabKey = 'all' | MemberRole;

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const gatewayStore = useGateway();
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();

const keyword = ref('');
const activeRole = ref<RoleTabKey>('all');
const isAddShow = ref(false);
const isChangeShow = ref(false);
const isModelShow = ref(false);
const changeMember = ref<IMember>();
const members = ref<IMember[]>([]);
const displayMembers = ref<IMember[]>([]);
const loading = ref(false);

let requestId = 0;

const apigwId = computed(() => Number(route.params.id));
const currentUsername = computed(() => userStore.info.username);
const adminCount = computed(() => members.value.filter(member => member.role === 'administrator').length);

const roleTabs = computed(() => [
  {
    key: 'all' as RoleTabKey,
    label: t('全部成员'),
    count: members.value.length,
  },
  {
    key: 'administrator' as RoleTabKey,
    label: t('管理员'),
    count: adminCount.value,
  },
  {
    key: 'operator' as RoleTabKey,
    label: t('运营者'),
    count: members.value.filter(item => item.role === 'operator').length,
  },
]);

const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    title: t('用户名'),
    colKey: 'username',
    width: 220,
    cell: (_h: unknown, { row }: { row: TableRowData }) => {
      const member = row as unknown as IMember;
      return featureFlagStore.isEnableDisplayName
        ? <span><bk-user-display-name user-id={member.username} /></span>
        : <span>{member.username}</span>;
    },
  },
  {
    title: t('角色'),
    colKey: 'role',
    width: 220,
    cell: (_h: unknown, { row }: { row: TableRowData }) => {
      const member = row as unknown as IMember;
      return (
        <bk-tag theme={member.role === 'administrator' ? 'success' : 'warning'}>
          {getRoleLabel(member.role)}
        </bk-tag>
      );
    },
  },
  {
    title: t('权限描述'),
    colKey: 'description',
    ellipsis: true,
    cell: (_h: unknown, { row }: { row: TableRowData }) => {
      const member = row as unknown as IMember;
      return getRoleDescription(member.role);
    },
  },
  {
    title: t('操作'),
    colKey: 'operation',
    width: 180,
    cell: (_h: unknown, { row }: { row: TableRowData }) => {
      const member = row as unknown as IMember;
      return (
        <div class="member-actions">
          <bk-button
            text
            theme="primary"
            onClick={() => handleChangeRole(member)}
          >
            {t('变更角色')}
          </bk-button>
          <bk-button
            text
            theme="primary"
            onClick={() => handleDelete(member)}
          >
            {t('删除成员')}
          </bk-button>
        </div>
      );
    },
  },
]);

watch(
  [members, activeRole, keyword],
  () => {
    displayMembers.value = members.value.filter((item) => {
      const matchRole = activeRole.value === 'all' || item.role === activeRole.value;
      const matchKeyword = !keyword.value || item.username.toLowerCase().includes(keyword.value.toLowerCase());
      return matchRole && matchKeyword;
    });
  },
  { immediate: true },
);

watch(apigwId, () => {
  members.value = [];
  isAddShow.value = false;
  isChangeShow.value = false;
  fetchMembers();
});

const handleAdd = () => {
  isAddShow.value = true;
};

const handleViewPermissionModel = () => {
  isModelShow.value = true;
};

const fetchMembers = async () => {
  const currentRequestId = ++requestId;
  loading.value = true;
  try {
    const result = await getGatewayMemberList(apigwId.value);
    if (currentRequestId === requestId) {
      members.value = result;
    }
  }
  catch {
    // 错误由统一 HTTP 封装提示，不保留可能过期的成员数据。
    if (currentRequestId === requestId) {
      members.value = [];
    }
  }
  finally {
    if (currentRequestId === requestId) {
      loading.value = false;
    }
  }
};

const handleMembersChanged = async (member?: IMember) => {
  if (member?.username === currentUsername.value) {
    // 自己被移除或降级后，成员接口不再可访问，且不能沿用旧管理员身份。
    gatewayStore.clearCurrentGateway();
    await router.replace({ name: 'Home' });
    return;
  }
  try {
    await Promise.all([fetchMembers(), gatewayStore.fetchGatewayDetail(apigwId.value)]);
  }
  catch {
    // 网关详情刷新失败时清理缓存，下次进入网关时重新获取。
    gatewayStore.clearCurrentGateway();
  }
};

const confirmSelfLeaveAdmin = (onConfirm: () => Promise<boolean>) => {
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: () => t('确认移除自己的管理员权限？'),
    subTitle: t('您已将自己从管理员列表中移除，移除后您将失去查看和编辑网关的权限。请确认！'),
    confirmText: t('确定'),
    cancelText: t('取消'),
    beforeClose: action => action === 'confirm' ? onConfirm() : true,
  });
};

const handleChangeRole = (row: IMember) => {
  changeMember.value = row;
  isChangeShow.value = true;
};

const handleDelete = (row: IMember) => {
  if (row.role === 'administrator' && adminCount.value <= 1) {
    Message({
      theme: 'error',
      message: t('至少保留一名管理员'),
    });
    return;
  }

  const persist = async () => {
    try {
      await deleteGatewayMember(apigwId.value, row.id);
    }
    catch {
      // 请求失败时不更新列表，也不退出当前网关。
      return false;
    }
    Message({
      theme: 'success',
      message: t('删除成功'),
    });
    await handleMembersChanged(row);
    return true;
  };

  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: () => t('确认删除成员？'),
    subTitle: t('删除后该成员将失去对应权限，请确认'),
    confirmText: t('删除'),
    cancelText: t('取消'),
    confirmButtonTheme: 'danger',
    beforeClose: (action) => {
      if (action !== 'confirm') {
        return true;
      }
      if (row.username === currentUsername.value && row.role === 'administrator') {
        confirmSelfLeaveAdmin(persist);
        return true;
      }
      return persist();
    },
  });
};

onMounted(fetchMembers);

onUnmounted(() => {
  requestId += 1;
});

</script>

<style lang="scss" scoped>
.member-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.search-input {
  width: 240px;
}

:deep(.member-actions) {
  display: flex;
  gap: 16px;
}
</style>
