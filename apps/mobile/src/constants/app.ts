/** App-wide constants. */
export const APP_NAME = 'AgroRadar';

export const STORAGE_KEYS = {
  authToken: 'auth.token',
  authUser: 'auth.user',
  themeMode: 'theme.mode',
} as const;

export const QUERY_KEYS = {
  health: ['health'] as const,
  user: (id: string) => ['user', id] as const,
} as const;

export const ROUTES = {
  home: '/',
} as const;
