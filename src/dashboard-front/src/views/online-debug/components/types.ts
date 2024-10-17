export interface RowType {
  id?: number;
  name: string;
  value: string;
  type: string;
  instructions: string;
  isEdit?: boolean;
  editType?: boolean;
  required?: boolean;
  options?: unknown;
  default?: string;
}

export interface TypeItem {
  label: string;
  value: string;
}

export interface SelectPayload {
  row: RowType;
  index: number;
  checked: boolean;
  data: RowType[];
}

type ColumnType = {
  field: string;
  index: number;
};

export interface CellClickPayload {
  event: Event;
  row: RowType;
  column: ColumnType;
  rowIndex: number;
  columnIndex: number;
}

export interface CellType {
  field: string;
  index: number;
  label: string;
  prop: string;
}
