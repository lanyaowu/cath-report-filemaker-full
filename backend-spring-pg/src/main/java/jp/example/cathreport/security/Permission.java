package jp.example.cathreport.security;

import java.util.Set;

/** 操作の権限と、それを持つ役割（Node.js 版 security.ts の PERMISSIONS と同じ） */
public enum Permission {
  READ("閲覧", "admin", "doctor", "secretary", "viewer"),
  EDIT("編集", "admin", "doctor", "secretary"),
  CONFIRM("確定・確定解除", "admin", "doctor"),
  VERIFY("照合", "admin", "doctor"),
  DELETE_REPORT("レポート削除", "admin", "doctor"),
  DELETE_PATIENT("患者削除", "admin"),
  MASTERS("マスタ編集", "admin"),
  SEED("サンプルデータ投入", "admin"),
  AUDIT("監査ログの閲覧", "admin");

  public final String label;
  public final Set<String> roles;

  Permission(String label, String... roles) {
    this.label = label;
    this.roles = Set.of(roles);
  }
}
