import jsYaml from 'js-yaml';

export const json2Yaml = (jsonStr: string) => {
  try {
    return {
      data: jsYaml.dump(JSON.parse(jsonStr)),
      error: false,
    };
  }
  catch {
    return {
      data: '',
      error: true,
    };
  }
};
