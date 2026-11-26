package jp.example.cathreport.security;

import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import jp.example.cathreport.audit.AuditService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

/** ログイン・ログアウト・自分の情報・監査ログ（Node.js 版と同じ API） */
@RestController
@RequestMapping("/api")
public class AuthController {
  private static final DateTimeFormatter HM = DateTimeFormatter.ofPattern("HH:mm").withZone(ZoneId.of("Asia/Tokyo"));

  private final UserStore users;
  private final TokenService tokens;
  private final AuditService audit;
  private final ApiAuthInterceptor auth;
  private final LoginThrottle throttle = new LoginThrottle(5, 15);

  public AuthController(UserStore users, TokenService tokens, AuditService audit, ApiAuthInterceptor auth) {
    this.users = users;
    this.tokens = tokens;
    this.audit = audit;
    this.auth = auth;
  }

  public static class LoginRequest {
    public String username;
    public String password;
  }

  @PostMapping("/auth/login")
  public Map<String, Object> login(@RequestBody LoginRequest req) {
    String name = req.username == null ? "" : req.username.trim();
    Map<String, Object> out = new LinkedHashMap<>();
    if (!auth.enabled()) {
      out.put("token", "auth-disabled");
      out.put("user", ApiAuthInterceptor.DEV_USER);
      return out;
    }
    long now = System.currentTimeMillis();
    Long until = throttle.lockedUntil(name, now);
    if (until != null) {
      audit.record("LOGIN_LOCKED", "user", name, "");
      throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS, "ログインに続けて失敗したため、" + HM.format(Instant.ofEpochMilli(until)) + " までログインできません");
    }
    AuthUser u = users.authenticate(name, req.password);
    if (u == null) {
      throttle.fail(name, now);
      audit.record("LOGIN_FAILURE", "user", name, "");
      throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "ユーザー名またはパスワードが違います");
    }
    throttle.success(name);
    AuthContext.set(u, AuthContext.ip());
    audit.record("LOGIN", "user", name, "");
    TokenService.Issued t = tokens.issue(u);
    out.put("token", t.token());
    out.put("expiresAt", t.expiresAt());
    out.put("user", u);
    return out;
  }

  @GetMapping("/auth/me")
  public AuthUser me() {
    return AuthContext.required();
  }

  @PostMapping("/auth/logout")
  public ResponseEntity<Void> logout() {
    audit.record("LOGOUT", "user", AuthContext.required().username(), "");
    return ResponseEntity.noContent().build();
  }

  /** 監査ログの検索（管理者のみ）。withChanges=true で変わった項目も返す */
  @GetMapping("/audit")
  public List<Map<String, Object>> search(
      @RequestParam(required = false) String from,
      @RequestParam(required = false) String to,
      @RequestParam(required = false) String username,
      @RequestParam(required = false) String action,
      @RequestParam(required = false) String targetType,
      @RequestParam(required = false) String targetId,
      @RequestParam(defaultValue = "false") boolean withChanges,
      @RequestParam(defaultValue = "500") int limit) {
    AuthContext.require(Permission.AUDIT);
    return audit.search(from, to, username, action, targetType, targetId, withChanges, Math.max(1, Math.min(limit, 5000)));
  }
}
