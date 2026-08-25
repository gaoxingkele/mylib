import { useLogStore, type LogLevel } from "./log-store";

export interface Logger {
  debug: (message: string, data?: unknown) => void;
  info: (message: string, data?: unknown) => void;
  warn: (message: string, data?: unknown) => void;
  error: (message: string, data?: unknown) => void;
}

/**
 * Create a scoped logger that writes to the structured log store.
 *
 * Usage:
 *   const log = createLogger("mupdf-page");
 *   log.info("Rendering page", { pageIndex, scale });
 */
export function createLogger(source: string): Logger {
  const log = (level: LogLevel, message: string, data?: unknown) => {
    useLogStore.getState().log(level, source, message, data);
  };

  return {
    debug: (message, data) => log("debug", message, data),
    info: (message, data) => log("info", message, data),
    warn: (message, data) => log("warn", message, data),
    error: (message, data) => log("error", message, data),
  };
}
