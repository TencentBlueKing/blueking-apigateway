/**
 * datepicker 时间选择器 hooks 适用于列表筛选
 */
import {
  ref,
  reactive,
} from 'vue';
import { useI18n } from 'vue-i18n';
export const useDatePicker = (filterData?: any) => {
  const { t } = useI18n();
  const shortcutsRange = reactive([
    {
      text: t('今天'),
      value() {
        const end = new Date();
        const start = new Date(end.getFullYear(), end.getMonth(), end.getDate());
        return [start, end];
      },
    },
    {
      text: t('近7天'),
      value() {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
        return [start, end];
      },
    },
    {
      text: t('近15天'),
      value() {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 15);
        return [start, end];
      },
    },
    {
      text: t('近30天'),
      value() {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
        return [start, end];
      },
    },
  ]);

  const dateValue = ref([]);

  const handleChange = (date: any) => {
    dateValue.value = date;
  };

  const handleComfirm = () => {
    setFilterDate(dateValue.value);
  };

  // 格式化时间
  const setFilterDate = (date: any[]) => {
    // @ts-ignore
    filterData.value.time_start = parseInt((+new Date(date[0])) / 1000, 10);
    // @ts-ignore
    filterData.value.time_end = parseInt((+new Date(date[1])) / 1000, 10);
  };

  return {
    shortcutsRange,
    dateValue,
    handleChange,
    handleComfirm,
  };
};
