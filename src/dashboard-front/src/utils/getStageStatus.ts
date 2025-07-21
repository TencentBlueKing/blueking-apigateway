// 环境状态
import type { IStageListItem } from '@/services/source/stage';

export const getStageStatus = (stageData?: IStageListItem | null) => {
  if (stageData?.status === 1) {
    return stageData?.release?.status;
  }
  if (stageData?.release?.status === 'unreleased') { // 未发布
    return 'unreleased';
  }
  return 'delist';
};
