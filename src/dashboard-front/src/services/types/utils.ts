export interface ICountAndResults<R> {
  count: number
  results: R[]
}

export type IExtractApiReturn<T extends (...args: any) => Promise<unknown>> = Awaited<ReturnType<T>>;

export type IExtractResults<R extends ICountAndResults<unknown>> = R['results'][number];

export type IExtractListApiResults<T extends (...args: any) => Promise<ICountAndResults<unknown>>> = IExtractApiReturn<T>['results'][number];
