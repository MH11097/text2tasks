/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_DEBUG?: string;
  readonly VITE_LOGGING_ENABLED?: string;
  readonly DEV?: boolean;
  readonly PROD?: boolean;
  readonly MODE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}