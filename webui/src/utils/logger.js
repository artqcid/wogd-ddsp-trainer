/**
 * Frontend logger.
 *
 * In dev mode (import.meta.env.DEV) all levels are visible.
 * In production only warn/error show.
 */
const LEVELS = { debug: 0, info: 1, warn: 2, error: 3 }
const currentLevel = import.meta.env.DEV ? LEVELS.debug : LEVELS.warn

function log(level, ...args) {
  if (LEVELS[level] < currentLevel) return
  const fn = level === 'error' ? console.error
    : level === 'warn' ? console.warn
    : level === 'info' ? console.info
    : console.debug
  fn(`[${level.toUpperCase()}]`, ...args)
}

export const logger = {
  debug: (...args) => log('debug', ...args),
  info: (...args) => log('info', ...args),
  warn: (...args) => log('warn', ...args),
  error: (...args) => log('error', ...args),
}
