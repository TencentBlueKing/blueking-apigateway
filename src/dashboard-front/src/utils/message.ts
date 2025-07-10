import { Message } from 'bkui-vue';

export const messageSuccess = (message: string, delay = 3000) => {
  Message({
    message,
    theme: 'success',
    delay,
  });
};

export const messageError = (message: string, delay = 3000) => {
  Message({
    message,
    theme: 'error',
    delay,
  });
};

export const messageWarn = (message: string, delay = 3000) => {
  Message({
    message,
    theme: 'warning',
    delay,
  });
};
