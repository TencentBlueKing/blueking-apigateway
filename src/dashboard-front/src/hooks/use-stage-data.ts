import { computed } from 'vue';
import { getStageList } from '@/http';
import { useStage } from '@/store';
import { useRoute } from 'vue-router';

export const useGetStageList = () => {
  const stage = useStage();
  const route = useRoute();
  const apigwId = computed(() => +route.params.id);

  const getStagesStatus = async () => {
    if (!apigwId.value) return;
    const res = await getStageList(apigwId.value);

    let notUpdatedStages = res?.filter((item: any) => {
      if (item.status === 1 && item.resource_version?.schema_version === '1.0') {
        return true;
      }
    });
    notUpdatedStages = notUpdatedStages?.map((item: any) => item?.name);

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
