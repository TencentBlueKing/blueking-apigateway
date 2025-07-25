<template>
  <div class="chat-box">
    <a
      href="javascript: void(0);"
      class="support-btn"
      @click="handleShowDialog"
    >
      <AgIcon
        name="doc-icon"
        size="16"
        class="doc-qw icon-ag-qw mr-3px"
      /> {{ t('一键拉群') }}
    </a>

    <BkDialog
      v-model:is-show="chatDialog.visible"
      width="600"
      header-align="left"
      theme="primary"
      :quick-close="false"
      :title="t('一键拉群')"
      @confirm="handleConfirm"
      @closed="handleCancel"
    >
      <div class="chat-dialog">
        <div class="header">
          <div class="icon">
            <AgIcon
              name="doc-icon"
              class="doc-qw icon-ag-qw"
            />
          </div>
          <div class="desc">
            <p> {{ t('一键拉群功能') }} </p>
            <p> {{ t('可以通过企业微信将需求的相关人员邀请到一个群里进行讨论') }} </p>
          </div>
        </div>
        <div v-bk-tooltips="{ content: userlist.join(', ') }">
          <BkInput
            :key="renderKey"
            v-model="userlist"
            :show-overflow-tooltips="false"
            :placeholder="t('请输入群成员')"
            class="chat-selector"
            disabled
          />
        </div>
      </div>
    </BkDialog>
  </div>
</template>

<script lang="ts" setup>
import {
  createChat,
  sendChat,
} from '@/services/source/chat';
import { useStage } from '@/stores';
import { Message } from 'bkui-vue';

interface IProps {
  name: string
  owner: string
  defaultUserList: string[]
  content: string
  isQuery: boolean
}

const {
  name = '',
  owner = '',
  defaultUserList = [] as string[],
  content = '',
  isQuery = false,
} = defineProps<IProps>();

const { t } = useI18n();
const stageStore = useStage();

const renderKey = ref<number>(0);
const chatDialog = reactive<any>({ visible: false });
const userlist = ref([...defaultUserList]);

const curStage = computed(() => stageStore.curStageData?.id);

const handleShowDialog = () => {
  chatDialog.visible = true;
};

const handleCancel = () => {
  chatDialog.visible = false;
};

const handleConfirm = async () => {
  let contentStr = content;
  if (isQuery) {
    const qeury = contentStr.split('?')[1];
    if (!qeury) {
      contentStr = `${contentStr}?stage=${curStage.value}`;
    }
  }
  if (!userlist.value?.length) {
    Message({
      theme: 'error',
      message: t('请选择群成员'),
    });
    return false;
  }

  // 创建群
  const body = {
    bk_app_code: 'create-chat',
    name: name,
    owner: owner,
    userlist: [...userlist.value, owner],
  };
  const res = await createChat(body);
  // 发送消息
  const chartId = res.data.chatid;

  const data = {
    bk_app_code: 'create-chat',
    chatid: chartId,
    msgtype: 'text',
    text: { content: contentStr },
  };
  await sendChat(data);
  Message({
    theme: 'success',
    message: t('创建成功'),
  });
};

watch(
  () => defaultUserList,
  () => {
    defaultUserList?.forEach((user: any) => {
      if (!userlist.value?.includes(user)) {
        userlist.value.push(user);
      }
    });
    renderKey.value += 1;
  },
);

</script>

<style lang="scss" scoped>
.chat-dialog {
  padding-bottom: 32px;
}

.chat-box {
  display: inline-block;
}

:deep(.chat-selector) {

  .bk-tag-input {
    min-height: 100px;
  }

  .bk-tag-selector .bk-tag-input {
    align-items: flex-start;
  }

  .clear-icon {
    display: none;
  }
}

.support-btn {
  display: inline-block;
  font-size: 12px;
  color: #3A84FF;
}

.header {
  display: flex;
  margin-bottom: 10px;

  .icon {
    width: 60px;
    font-size: 50px;
    line-height: 1;
    text-align: left;
  }

  .desc {
    flex: 1;
    padding-top: 10px;

    p {
      margin-bottom: 10px;
      font-size: 14px;
      line-height: 1;
    }
  }
}
</style>
