export const getMethodsTheme = (methods: string) => {
  if (!methods) return 'success';

  let theme = '';
  switch (methods.toLocaleLowerCase()) {
    case 'get':
      theme = 'success';
      break;
    case 'patch':
    case 'post':
      theme = 'info';
      break;
    case 'put':
      theme = 'warning';
      break;
    case 'delete':
      theme = 'danger';
      break;
  }
  return theme;
};
