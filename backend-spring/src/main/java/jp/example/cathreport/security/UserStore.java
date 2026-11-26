package jp.example.cathreport.security;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

/**
 * 利用者の定義（JSON）。app.auth.users-file（環境変数 AUTH_USERS_FILE）のファイル、未指定ならクラスパスの
 * sample-data/users.json（デモ用。本番では必ず差し替える）。形式は Node.js 版と共通。
 */
@Component
public class UserStore {
  private static final Logger log = LoggerFactory.getLogger(UserStore.class);

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class UserDef {
    public String username;
    public String displayName;
    public List<String> roles = new ArrayList<>();
    public String password;
    public boolean disabled;
  }

  private final Map<String, UserDef> users = new LinkedHashMap<>();

  public UserStore(ObjectMapper mapper, @Value("${app.auth.users-file:}") String usersFile) throws IOException {
    List<UserDef> list;
    if (usersFile != null && !usersFile.isBlank()) {
      try (InputStream in = Files.newInputStream(Path.of(usersFile))) {
        list = mapper.readValue(in, new TypeReference<List<UserDef>>() {});
      }
    } else {
      try (InputStream in = new ClassPathResource("sample-data/users.json").getInputStream()) {
        list = mapper.readValue(in, new TypeReference<List<UserDef>>() {});
      }
      log.warn("AUTH_USERS_FILE が未指定のため、デモ用の利用者（sample-data/users.json）を使います。本番では必ず差し替えてください");
    }
    for (UserDef u : list) if (u.username != null && !u.disabled) users.put(u.username, u);
    log.info("利用者 {} 名を読み込みました", users.size());
  }

  /** パスワードが正しければ利用者を返す */
  public AuthUser authenticate(String username, String password) {
    UserDef u = users.get(username);
    if (u == null || !PasswordHasher.verify(password, u.password)) return null;
    return toUser(u);
  }

  /** 現在の定義（無効化・削除された利用者は null） */
  public AuthUser find(String username) {
    UserDef u = users.get(username);
    return u == null ? null : toUser(u);
  }

  private static AuthUser toUser(UserDef u) {
    return new AuthUser(u.username, u.displayName == null ? u.username : u.displayName, List.copyOf(u.roles));
  }
}
