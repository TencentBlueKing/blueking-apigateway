/**
 * 选择相关状态和事件
 */
import {
  ref,
} from 'vue';

type SelectionType = {
  checked: boolean;
  data: any[];
  isAll?: boolean;
  row?: any
};

export const useSelection = () => {
  const selections = ref([]);
  const bkTableRef = ref();

  const handleSelectionChange = (selection: SelectionType) => {
    // 选择某一个
    if (selection.checked) {
      selections.value.push(selection.row);
    }
    // 取消选择某一个
    if (!selection.checked) {
      const index = selections.value.findIndex((item: any) => item.id === selection.row.id);
      selections.value.splice(index, 1);
    }
  };

  const handleSelecAllChange = (selection: SelectionType) => {
    if (selection.checked) {
      selections.value = JSON.parse(JSON.stringify(selection.data));
    } else {
      selections.value = [];
    }
  };

  const resetSelections = () => {
    selections.value = [];
    bkTableRef.value?.clearSelection();
  };

  return {
    selections,
    bkTableRef,
    handleSelectionChange,
    handleSelecAllChange,
    resetSelections,
  };
};
