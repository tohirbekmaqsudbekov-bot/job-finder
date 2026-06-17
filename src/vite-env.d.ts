/// <reference types="vite/client" />

declare module '*.csv?raw' {
  const value: string;
  export default value;
}

declare interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

declare interface ImportMeta {
  readonly env: ImportMetaEnv;
}