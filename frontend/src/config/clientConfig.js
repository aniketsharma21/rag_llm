const DEFAULTS = {
  apiBaseUrl: 'http://localhost:8000',
  websocketPath: '/ws/chat',
  websocketUrl: 'ws://localhost:8000/ws/chat',
  jobStatusPollInterval: 2000,
  maxReconnectDelay: 30000,
};

const ensureNoTrailingSlash = (value) => {
  if (!value) {
    return value;
  }
  return value.endsWith('/') ? value.slice(0, -1) : value;
};

const parseIntegerEnv = (value, fallback) => {
  const parsed = Number.parseInt(value ?? '', 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

export const createClientConfig = () => {
  const rawApiBase = process.env.REACT_APP_API_URL
    ?? process.env.REACT_APP_API_BASE
    ?? DEFAULTS.apiBaseUrl;

  const apiBaseUrl = ensureNoTrailingSlash(rawApiBase.trim());

  const rawWebsocketUrl = process.env.REACT_APP_WS_URL;

  const websocketUrl = rawWebsocketUrl && rawWebsocketUrl.trim()
    ? rawWebsocketUrl.trim()
    : (() => {
        try {
          const apiUrl = new URL(apiBaseUrl);
          const wsProtocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
          return `${wsProtocol}//${apiUrl.host}${DEFAULTS.websocketPath}`;
        } catch (error) {
          return DEFAULTS.websocketUrl;
        }
      })();

  const jobStatusPollInterval = parseIntegerEnv(
    process.env.REACT_APP_JOB_POLL_INTERVAL,
    DEFAULTS.jobStatusPollInterval,
  );

  const maxReconnectDelay = parseIntegerEnv(
    process.env.REACT_APP_WS_MAX_RECONNECT_DELAY,
    DEFAULTS.maxReconnectDelay,
  );

  return {
    apiBaseUrl,
    websocketUrl,
    jobStatusPollInterval,
    maxReconnectDelay,
  };
};
