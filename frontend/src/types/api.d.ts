// Extend AxiosRequestConfig to include metadata
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      startTime: number;
      requestId: string;
    };
  }
}