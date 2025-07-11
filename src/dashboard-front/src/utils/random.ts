import { random as _random } from 'lodash-es';

export const random = () => `${_random(0, 999999)}_${Date.now()}_${_random(0, 999999)}`;
