export * from '../../electron/types';

export type ActiveTab = 'tournaments' | 'timeline' | 'pipeline' | 'seo' | 'settings';

export interface AppNotification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
}
