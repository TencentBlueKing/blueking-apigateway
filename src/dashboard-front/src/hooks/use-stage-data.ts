import { getStageList } from '@/http';
import { useStage, useCommon } from '@/store';

export const useGetStageList = () => {
  const stage = useStage();
  const common = useCommon();
  const { apigwId } = common;
  const getStagesStatus = async () => {
    if (!apigwId) return;
    const res = await getStageList(apigwId);

    const notUpdatedStages = res?.filter((item: any) => {
      if (item.status === 1 && item.resource_version?.schema_version === '1.0') {
        return true;
      }
    });
    let exist2 = false;
    for (let i = 0; i < res?.length; i++) {
      const item = res[i];
      if (item.schema_version === '2.0') {
        exist2 = true;
        break;
      }
    }

    stage.setNotUpdatedStages(notUpdatedStages);
    stage.setExist2(exist2);

    return {
      notUpdatedStages,
      exist2,
    };
  };

  return {
    getStagesStatus,
  };
};
