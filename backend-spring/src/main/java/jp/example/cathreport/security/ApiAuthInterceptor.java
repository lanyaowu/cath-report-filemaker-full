package jp.example.cathreport.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * /api/** の認証（Authorization: Bearer トークン）。GET /api/health・POST /api/auth/login・OPTIONS は対象外。
 * app.auth.enabled=false（AUTH_ENABLED=false）なら認証なし（開発専用。全操作を管理者として扱う）。
 */
@Component
public class ApiAuthInterceptor implements HandlerInterceptor {
  private static final Logger log = LoggerFactory.getLogger(ApiAuthInterceptor.class);
  public static final AuthUser DEV_USER = new AuthUser("dev", "開発ユーザー（認証なし）", List.of("admin"));

  private final TokenService tokens;
  private final UserStore users;
  private final ObjectMapper mapper;
  private final boolean enabled;

  public ApiAuthInterceptor(TokenService tokens, UserStore users, ObjectMapper mapper, @Value("${app.auth.enabled:true}") boolean enabled) {
    this.tokens = tokens;
    this.users = users;
    this.mapper = mapper;
    this.enabled = enabled;
    if (!enabled) log.warn("AUTH_ENABLED=false：認証なしで動作します（開発専用）");
  }

  public boolean enabled() {
    return enabled;
  }

  @Override
  public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) throws Exception {
    String path = req.getRequestURI().substring(req.getContextPath().length());
    String m = req.getMethod();
    if ("OPTIONS".equals(m) || ("GET".equals(m) && path.equals("/api/health")) || ("POST".equals(m) && path.equals("/api/auth/login"))) {
      AuthContext.set(null, req.getRemoteAddr());
      return true;
    }
    if (!enabled) {
      AuthContext.set(DEV_USER, req.getRemoteAddr());
      return true;
    }
    String h = req.getHeader("Authorization");
    AuthUser t = h != null && h.startsWith("Bearer ") ? tokens.verify(h.substring(7)) : null;
    AuthUser current = t == null ? null : users.find(t.username()); // 役割は最新の定義を使う（無効化された利用者は拒否）
    if (current == null) {
      res.setStatus(401);
      res.setContentType("application/json;charset=UTF-8");
      mapper.writeValue(res.getOutputStream(), Map.of("error", "ログインが必要です（期限切れの場合は再ログインしてください）"));
      return false;
    }
    AuthContext.set(current, req.getRemoteAddr());
    return true;
  }

  @Override
  public void afterCompletion(HttpServletRequest req, HttpServletResponse res, Object handler, Exception ex) {
    AuthContext.clear();
  }
}
