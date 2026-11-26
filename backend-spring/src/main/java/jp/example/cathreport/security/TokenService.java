package jp.example.cathreport.security;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * アクセストークン：base64url(JSON {sub,name,roles,exp}) + "." + base64url(HMAC-SHA256)。Node.js 版と同じ形式。
 * 鍵は app.auth.secret（環境変数 AUTH_SECRET）。未設定なら起動ごとに乱数（再起動でログアウト）。
 */
@Component
public class TokenService {
  private static final Logger log = LoggerFactory.getLogger(TokenService.class);
  private static final Base64.Encoder ENC = Base64.getUrlEncoder().withoutPadding();
  private static final Base64.Decoder DEC = Base64.getUrlDecoder();

  private final byte[] secret;
  private final long ttlSeconds;
  private final ObjectMapper mapper;

  public TokenService(ObjectMapper mapper, @Value("${app.auth.secret:}") String secret, @Value("${app.auth.token-ttl-minutes:480}") long ttlMinutes) {
    this.mapper = mapper;
    if (secret == null || secret.isBlank()) {
      byte[] r = new byte[32];
      new SecureRandom().nextBytes(r);
      this.secret = r;
      log.warn("AUTH_SECRET が未設定のため、起動ごとに鍵を生成します（再起動でログアウトされます）");
    } else {
      this.secret = secret.getBytes(StandardCharsets.UTF_8);
    }
    this.ttlSeconds = ttlMinutes * 60;
  }

  public record Issued(String token, String expiresAt) {}

  public Issued issue(AuthUser u) {
    long exp = Instant.now().getEpochSecond() + ttlSeconds;
    Map<String, Object> p = new LinkedHashMap<>();
    p.put("sub", u.username());
    p.put("name", u.displayName());
    p.put("roles", u.roles());
    p.put("exp", exp);
    try {
      String payload = ENC.encodeToString(mapper.writeValueAsBytes(p));
      return new Issued(payload + "." + ENC.encodeToString(sign(payload)), Instant.ofEpochSecond(exp).toString());
    } catch (com.fasterxml.jackson.core.JsonProcessingException e) {
      throw new IllegalStateException(e);
    }
  }

  /** 正しいトークンなら利用者（署名不一致・期限切れ・形式不正は null） */
  public AuthUser verify(String token) {
    if (token == null) return null;
    String[] t = token.split("\\.", -1);
    if (t.length != 2) return null;
    try {
      if (!MessageDigest.isEqual(sign(t[0]), DEC.decode(t[1]))) return null;
      JsonNode p = mapper.readTree(DEC.decode(t[0]));
      if (!p.path("exp").isNumber() || p.path("exp").asLong() <= Instant.now().getEpochSecond()) return null;
      List<String> roles = new ArrayList<>();
      p.path("roles").forEach(r -> roles.add(r.asText()));
      return new AuthUser(p.path("sub").asText(), p.path("name").asText(), roles);
    } catch (Exception e) {
      return null;
    }
  }

  private byte[] sign(String data) {
    try {
      Mac mac = Mac.getInstance("HmacSHA256");
      mac.init(new SecretKeySpec(secret, "HmacSHA256"));
      return mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
    } catch (java.security.GeneralSecurityException e) {
      throw new IllegalStateException(e);
    }
  }
}
