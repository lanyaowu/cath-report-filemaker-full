package jp.example.cathreport.security;

import java.util.List;

/** ログイン中の利用者 */
public record AuthUser(String username, String displayName, List<String> roles) implements java.io.Serializable {
  public boolean can(Permission p) {
    return roles != null && roles.stream().anyMatch(p.roles::contains);
  }
}
