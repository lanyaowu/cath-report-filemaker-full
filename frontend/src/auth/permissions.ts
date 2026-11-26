/** 役割と権限（サーバーと同じ表。画面ではボタンの無効化に使い、最終的な判断はサーバーが行う） */
export type Role = 'admin' | 'doctor' | 'secretary' | 'viewer';
export type Permission = 'read' | 'edit' | 'confirm' | 'verify' | 'deleteReport' | 'deletePatient' | 'masters' | 'seed' | 'audit';

export interface AuthUser {
  username: string;
  displayName: string;
  roles: Role[];
}

export const PERMISSIONS: Record<Permission, Role[]> = {
  read: ['admin', 'doctor', 'secretary', 'viewer'],
  edit: ['admin', 'doctor', 'secretary'],
  confirm: ['admin', 'doctor'],
  verify: ['admin', 'doctor'],
  deleteReport: ['admin', 'doctor'],
  deletePatient: ['admin'],
  masters: ['admin'],
  seed: ['admin'],
  audit: ['admin'],
};

export const ROLE_LABEL: Record<Role, string> = { admin: '管理者', doctor: '医師', secretary: '秘書', viewer: '閲覧' };

export const hasPermission = (u: AuthUser | null | undefined, p: Permission) => !!u && u.roles.some((r) => PERMISSIONS[p]?.includes(r));
