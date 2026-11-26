package jp.example.cathreport.audit;

import java.sql.PreparedStatement;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import jp.example.cathreport.security.AuthContext;
import jp.example.cathreport.security.AuthUser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

/**
 * 監査ログ（テーブル audit_log・audit_change。V3__audit.sql・V5__audit_change.sql。トリガーで更新・削除を禁止）。
 * 業務の更新とは別に記録する（呼び出し元のトランザクションの外＝コントローラーから呼ぶ）。
 * 1 件の記録（audit_log）と、その変わった項目（audit_change）は 1 つのトランザクションで書く。
 */
@Service
public class AuditService {
  private static final Logger log = LoggerFactory.getLogger(AuditService.class);
  private final JdbcTemplate jdbc;
  private final TransactionTemplate tx;

  public AuditService(JdbcTemplate jdbc, TransactionTemplate tx) {
    this.jdbc = jdbc;
    this.tx = tx;
  }

  /** 記録する（失敗しても業務は止めず、サーバーのログに残す） */
  public void record(String action, String targetType, String targetId, String detail) {
    record(action, targetType, targetId, detail, List.of());
  }

  /** 変わった項目も記録する */
  public void record(String action, String targetType, String targetId, String detail, List<AuditDiff.Change> changes) {
    AuthUser u = AuthContext.user();
    List<AuditDiff.Change> ch = changes == null ? List.of() : changes;
    try {
      tx.executeWithoutResult(s -> {
        KeyHolder kh = new GeneratedKeyHolder();
        jdbc.update(con -> {
          PreparedStatement ps = con.prepareStatement(
              "INSERT INTO audit_log (username, display_name, action, target_type, target_id, detail, ip, change_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              new String[] {"id"});
          ps.setString(1, u == null ? "" : u.username());
          ps.setString(2, u == null ? "" : u.displayName());
          ps.setString(3, action);
          ps.setString(4, nz(targetType));
          ps.setString(5, nz(targetId));
          ps.setString(6, nz(detail));
          ps.setString(7, AuthContext.ip());
          ps.setInt(8, ch.size());
          return ps;
        }, kh);
        if (ch.isEmpty()) return;
        long id = kh.getKey().longValue();
        List<Object[]> rows = new ArrayList<>();
        for (int i = 0; i < ch.size(); i++) rows.add(new Object[] {id, i, ch.get(i).path(), ch.get(i).before(), ch.get(i).after()});
        jdbc.batchUpdate("INSERT INTO audit_change (audit_id, seq, path, before_value, after_value) VALUES (?, ?, ?, ?, ?)", rows);
      });
    } catch (RuntimeException e) {
      log.error("監査ログの記録に失敗しました: action={} target={}/{} user={} changes={}", action, targetType, targetId, u == null ? "" : u.username(), ch.size(), e);
    }
  }

  private static final String COLS = """
      SELECT id AS "_id", CAST(id AS text) AS "id", to_char(at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS "at",
             username AS "username", display_name AS "displayName", action AS "action", target_type AS "targetType",
             target_id AS "targetId", detail AS "detail", ip AS "ip", change_count AS "changeCount"
        FROM audit_log""";

  /** 検索（新しい順）。from・to は日付（YYYY-MM-DD、日本時間）。withChanges で変わった項目も返す */
  public List<Map<String, Object>> search(String from, String to, String username, String action, String targetType, String targetId,
      boolean withChanges, int limit) {
    StringBuilder sql = new StringBuilder(COLS).append(" WHERE true");
    List<Object> args = new ArrayList<>();
    if (from != null && !from.isBlank()) {
      sql.append(" AND at >= (CAST(? AS date)::timestamp AT TIME ZONE 'Asia/Tokyo')");
      args.add(from);
    }
    if (to != null && !to.isBlank()) {
      sql.append(" AND at < ((CAST(? AS date) + 1)::timestamp AT TIME ZONE 'Asia/Tokyo')");
      args.add(to);
    }
    eq(sql, args, "username", username);
    eq(sql, args, "action", action);
    eq(sql, args, "target_type", targetType);
    eq(sql, args, "target_id", targetId);
    sql.append(" ORDER BY at DESC, id DESC LIMIT ").append(limit);
    List<Map<String, Object>> list = jdbc.queryForList(sql.toString(), args.toArray());
    if (withChanges) attachChanges(list);
    list.forEach(m -> m.remove("_id"));
    return list;
  }

  /** レポートの変更履歴：そのレポートと患者の作成・削除と、項目が変わった更新（変わった項目つき。新しい順） */
  public List<Map<String, Object>> reportHistory(String reportId, String patientRef) {
    String sql = COLS + """
         WHERE ((target_type = 'report' AND target_id = ?) OR (target_type = 'patient' AND target_id = ?))
           AND (action LIKE 'CREATE%' OR action LIKE 'DELETE%' OR change_count > 0)
         ORDER BY at DESC, id DESC LIMIT 1000""";
    List<Map<String, Object>> list = jdbc.queryForList(sql, reportId, patientRef == null ? "" : patientRef);
    attachChanges(list);
    list.forEach(m -> m.remove("_id"));
    return list;
  }

  private void attachChanges(List<Map<String, Object>> list) {
    List<Object> ids = list.stream().filter(m -> ((Number) m.get("changeCount")).intValue() > 0).map(m -> m.get("_id")).toList();
    Map<Long, List<Map<String, Object>>> by = new LinkedHashMap<>();
    if (!ids.isEmpty()) {
      String in = String.join(",", Collections.nCopies(ids.size(), "?"));
      for (Map<String, Object> r : jdbc.queryForList(
          "SELECT audit_id, path, before_value, after_value FROM audit_change WHERE audit_id IN (" + in + ") ORDER BY audit_id, seq", ids.toArray())) {
        Map<String, Object> c = new LinkedHashMap<>();
        c.put("path", r.get("path"));
        c.put("before", r.get("before_value"));
        c.put("after", r.get("after_value"));
        by.computeIfAbsent(((Number) r.get("audit_id")).longValue(), k -> new ArrayList<>()).add(c);
      }
    }
    for (Map<String, Object> m : list) m.put("changes", by.getOrDefault(((Number) m.get("_id")).longValue(), List.of()));
  }

  private static void eq(StringBuilder sql, List<Object> args, String col, String v) {
    if (v != null && !v.isBlank()) {
      sql.append(" AND ").append(col).append(" = ?");
      args.add(v);
    }
  }

  private static String nz(String s) {
    return s == null ? "" : s;
  }
}
