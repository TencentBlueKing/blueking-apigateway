import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { InfoBox } from 'bkui-vue';

export function useSidebar() {
  const { t } = useI18n();
  const initDataStr = ref('');
  // const isBackDialogShow = ref(false);

  const initSidebarFormData = (data?: any) => {
    initDataStr.value = JSON.stringify(data);
  };

  const isSidebarClosed = (targetDataStr?: any) => {
    let isEqual = initDataStr.value === targetDataStr;
    if (typeof targetDataStr !== 'string') {
      // 数组长度对比
      const initData = JSON.parse(initDataStr.value);
      isEqual = initData.length === targetDataStr.length;
    }
    return new Promise((resolve) => {
      // 未编辑
      if (isEqual) {
        resolve(true);
      } else {
        // isBackDialogShow.value = true;
        // 已编辑
        InfoBox({
          'ext-cls': 'sideslider-close-cls',
          title: t('确认离开当前页？'),
          subTitle: t('离开将会导致未保存信息丢失'),
          confirmText: t('离开'),
          onConfirm() {
            resolve(true);
            // isBackDialogShow.value = false;
          },
          onClosed() {
            resolve(false);
            // isBackDialogShow.value = false;
          },
        });
      }
    });
  };

  return {
    initSidebarFormData,
    isSidebarClosed,
    // isBackDialogShow,
  };
};
