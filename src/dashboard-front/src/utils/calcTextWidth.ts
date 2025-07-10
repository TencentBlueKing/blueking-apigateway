export const calcTextWidth = (text: string, parentEl = document.body) => {
  const $el = document.createElement('div');
  $el.innerText = text;
  $el.style.position = 'absolute';
  $el.style.width = 'auto';
  $el.style.opacity = '0';
  $el.style.zIndex = '-1';
  $el.style.whiteSpace = 'pre';
  $el.style.wordBreak = 'no-break';
  parentEl.appendChild($el);
  const { width } = $el.getBoundingClientRect();
  parentEl.removeChild($el);

  return width;
};

export const calcTextHeight = (text: string, width: number, lineHeight = 40, parentEl = document.body) => {
  const $el = document.createElement('div');
  $el.innerText = text;
  $el.style.position = 'absolute';
  $el.style.width = `${width}px`;
  $el.style.opacity = '0';
  $el.style.zIndex = '-1';
  $el.style.whiteSpace = 'pre-wrap';
  $el.style.lineHeight = `${lineHeight}px`;
  parentEl.appendChild($el);
  const { height } = $el.getBoundingClientRect();
  parentEl.removeChild($el);

  return height;
};
