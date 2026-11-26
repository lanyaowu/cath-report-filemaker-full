package jp.example.cathreport.security;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

/**
 * レポート保存時の業務ルール（サーバー側で強制。Node.js 版 rules.ts と同じ仕様）。
 * old・neu は同じ方法で JSON 化したレポート（新規は old = null）。
 */
public final class ReportRules {
  public static final String LOCKED = "確定";
  /** 比較の対象外：確定済みでも変更できる項目と、サーバーが管理する項目 */
  private static final Set<String> IGNORE_TOP = Set.of("id", "status", "verified", "history", "version", "createdAt", "updatedAt");
  private static final Set<String> IGNORE_HEADER = Set.of("registrant");

  private ReportRules() {}

  public static void check(AuthUser u, JsonNode old, JsonNode neu) {
    require(u, Permission.EDIT);
    String oldStatus = old == null ? "入力中" : text(old.get("status"), "入力中");
    String newStatus = text(neu.get("status"), "入力中");
    if (!oldStatus.equals(newStatus)) require(u, Permission.CONFIRM);
    boolean oldVerified = old != null && old.path("verified").asBoolean(false);
    if (oldVerified != neu.path("verified").asBoolean(false)) require(u, Permission.VERIFY);
    if (old == null) return;
    if (LOCKED.equals(oldStatus) && LOCKED.equals(newStatus) && !lockedContent(old).equals(lockedContent(neu))) {
      throw new ResponseStatusException(HttpStatus.CONFLICT, "確定済みのため編集できません（ステータスを「入力中」に戻してください）");
    }
    JsonNode oh = old.path("history"), nh = neu.path("history");
    int on = oh.isArray() ? oh.size() : 0;
    boolean ok = (nh.isArray() ? nh.size() : 0) >= on;
    for (int i = 0; ok && i < on; i++) ok = oh.get(i).equals(nh.get(i));
    if (!ok) throw new ResponseStatusException(HttpStatus.CONFLICT, "登録履歴は変更・削除できません（追加のみ）");
  }

  public static void require(AuthUser u, Permission p) {
    if (u == null) throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "ログインが必要です");
    if (!u.can(p)) throw new ResponseStatusException(HttpStatus.FORBIDDEN, "この操作の権限がありません（" + p.label + "）");
  }

  private static ObjectNode lockedContent(JsonNode r) {
    ObjectNode o = ((ObjectNode) r).deepCopy();
    o.remove(IGNORE_TOP);
    JsonNode h = o.get("header");
    if (h instanceof ObjectNode hh) hh.remove(IGNORE_HEADER);
    removeNulls(o); // null の項目は無いものとみなす
    return o;
  }

  private static void removeNulls(JsonNode n) {
    if (n instanceof ObjectNode o) {
      java.util.List<String> nulls = new java.util.ArrayList<>();
      o.fields().forEachRemaining(e -> {
        if (e.getValue().isNull()) nulls.add(e.getKey());
        else removeNulls(e.getValue());
      });
      o.remove(nulls);
    } else if (n != null && n.isArray()) {
      n.forEach(ReportRules::removeNulls);
    }
  }

  private static String text(JsonNode n, String def) {
    return n == null || n.isNull() || n.asText().isEmpty() ? def : n.asText();
  }

  /** 楽観ロック：保存済みの version（無ければ 0）と送られた version を照合し、次の version を返す */
  public static long nextVersion(String kind, boolean exists, Long stored, Long sent) {
    if (!exists) return 0;
    long cur = stored == null ? 0 : stored;
    if (sent == null) throw new ResponseStatusException(HttpStatus.CONFLICT, "version が必要です（この" + kind + "を再読み込みしてから保存してください）");
    if (sent != cur) throw new ResponseStatusException(HttpStatus.CONFLICT, "この" + kind + "は他の端末で更新されています。再読み込みしてください");
    return cur + 1;
  }
}
