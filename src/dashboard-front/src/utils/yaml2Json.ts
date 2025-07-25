import jsYaml from 'js-yaml';

export const yaml2Json = (yamlStr: string) => {
  yamlStr = yamlStr.replace(/\|-(?!\s*\n)/g, '|-\n');
  try {
    return {
      data: jsYaml.load(yamlStr),
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
