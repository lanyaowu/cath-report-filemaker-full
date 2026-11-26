package jp.example.cathreport.security;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

/** 処理中のリクエストの利用者（インターセプターが設定し、完了時に消す） */
public final class AuthContext {
  private static final ThreadLocal<AuthUser> USER = new ThreadLocal<>();
  private static final ThreadLocal<String> IP = new ThreadLocal<>();

  private AuthContext() {}

  public static void set(AuthUser user, String ip) {
    USER.set(user);
    IP.set(ip);
  }

  public static void clear() {
    USER.remove();
    IP.remove();
  }

  /** 利用者（バッチ処理など、リクエスト外では null） */
  public static AuthUser user() {
    return USER.get();
  }

  public static String ip() {
    return IP.get() == null ? "" : IP.get();
  }

  /** ログイン中の利用者。未ログインは 401 */
  public static AuthUser required() {
    AuthUser u = USER.get();
    if (u == null) throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "ログインが必要です");
    return u;
  }

  /** 権限がなければ 403 */
  public static AuthUser require(Permission p) {
    AuthUser u = required();
    if (!u.can(p)) throw new ResponseStatusException(HttpStatus.FORBIDDEN, "この操作の権限がありません（" + p.label + "）");
    return u;
  }
}
