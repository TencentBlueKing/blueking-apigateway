import { Message } from 'bkui-vue';
import { t } from '@/locales';

export function copy(value: string) {
  if (!value) {
    Message({
      theme: 'warning',
      message: t('暂无可复制数据'),
      delay: 2000,
      dismissable: false,
    });
    return;
  }
  const el = document.createElement('textarea');
  el.value = value;
  el.setAttribute('readonly', '');
  el.style.position = 'absolute';
  el.style.left = '-9999px';
  document.body.appendChild(el);
  const selected = document.getSelection().rangeCount > 0 ? document.getSelection().getRangeAt(0) : false;
  el.select();
  document.execCommand('copy');
  document.body.removeChild(el);
  if (selected) {
    document.getSelection().removeAllRanges();
    document.getSelection().addRange(selected);
  }
  Message({
    theme: 'success',
    width: 'auto',
    message: t('复制成功'),
    delay: 2000,
    dismissable: false,
  });
}
