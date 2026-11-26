package jp.example.cathreport.audit;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import jp.example.cathreport.security.AuthContext;
import jp.example.cathreport.security.AuthUser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Service;

/** 監査ログ（collection: audit_log。追加のみ） */
@Service
public class AuditService {
  private static final Logger log = LoggerFactory.getLogger(AuditService.class);
  public static final String COLLECTION = "audit_log";
  private final MongoTemplate mongo;

  public AuditService(MongoTemplate mongo) {
    this.mongo = mongo;
  }

  /** 記録する（失敗しても業務は止めず、サーバーのログに残す） */
  public void record(String action, String targetType, String targetId, String detail) {
    record(action, targetType, targetId, detail, List.of());
  }

  /** 変わった項目（パス・変更前・変更後）も 1 つのドキュメントに記録する */
  public void record(String action, String targetType, String targetId, String detail, List<AuditDiff.Change> changes) {
    AuthUser u = AuthContext.user();
    Map<String, Object> d = new LinkedHashMap<>();
    d.put("at", Instant.now().toString());
    d.put("username", u == null ? "" : u.username());
    d.put("displayName", u == null ? "" : u.displayName());
    d.put("action", action);
    d.put("targetType", targetType);
    d.put("targetId", targetId == null ? "" : targetId);
    d.put("detail", detail == null ? "" : detail);
    d.put("ip", AuthContext.ip());
    List<AuditDiff.Change> ch = changes == null ? List.of() : changes;
    d.put("changeCount", ch.size());
    if (!ch.isEmpty()) {
      List<Map<String, Object>> list = new ArrayList<>();
      for (AuditDiff.Change c : ch) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("path", c.path());
        m.put("before", c.before());
        m.put("after", c.after());
        list.add(m);
      }
      d.put("changes", list);
    }
    try {
      mongo.insert(d, COLLECTION);
    } catch (RuntimeException e) {
      log.error("監査ログの記録に失敗しました: {}", d, e);
    }
  }

  /** 検索（新しい順）。from・to は日付（YYYY-MM-DD、日本時間）。withChanges で変わった項目も返す */
  public List<Map<String, Object>> search(String from, String to, String username, String action, String targetType, String targetId,
      boolean withChanges, int limit) {
    Query q = new Query();
    boolean f = from != null && !from.isBlank(), t = to != null && !to.isBlank();
    if (f || t) {
      Criteria c = Criteria.where("at");
      if (f) c = c.gte(jst(from, 0));
      if (t) c = c.lt(jst(to, 1));
      q.addCriteria(c);
    }
    eq(q, "username", username);
    eq(q, "action", action);
    eq(q, "targetType", targetType);
    eq(q, "targetId", targetId);
    if (!withChanges) q.fields().exclude("changes");
    q.with(Sort.by(Sort.Direction.DESC, "at").and(Sort.by(Sort.Direction.DESC, "_id"))).limit(limit);
    return out(q);
  }

  /** レポートの変更履歴：そのレポートと患者の作成・削除と、項目が変わった更新（変わった項目つき。新しい順） */
  public List<Map<String, Object>> reportHistory(String reportId, String patientRef) {
    Criteria target = new Criteria().orOperator(
        Criteria.where("targetType").is("report").and("targetId").is(reportId),
        Criteria.where("targetType").is("patient").and("targetId").is(patientRef == null ? "" : patientRef));
    Criteria kind = new Criteria().orOperator(Criteria.where("action").regex("^(CREATE|DELETE)_"), Criteria.where("changeCount").gt(0));
    Query q = new Query(new Criteria().andOperator(target, kind));
    q.with(Sort.by(Sort.Direction.DESC, "at").and(Sort.by(Sort.Direction.DESC, "_id"))).limit(1000);
    return out(q);
  }

  /** API の形：_id を id（文字列）に。変更の記録を始める前の記録は changeCount 0 */
  @SuppressWarnings({"unchecked", "rawtypes"})
  private List<Map<String, Object>> out(Query q) {
    List<Map<String, Object>> list = new ArrayList<>();
    for (Map d : mongo.find(q, Map.class, COLLECTION)) {
      Map<String, Object> m = new LinkedHashMap<>();
      m.put("id", String.valueOf(d.remove("_id")));
      m.put("changeCount", 0);
      m.putAll(d);
      list.add(m);
    }
    return list;
  }

  private static void eq(Query q, String field, String v) {
    if (v != null && !v.isBlank()) q.addCriteria(Criteria.where(field).is(v));
  }

  /** 日本時間の日付（YYYY-MM-DD）の 0 時（+days 日）を UTC の ISO 文字列に（at は UTC の ISO 文字列で保存） */
  static String jst(String date, int days) {
    return java.time.LocalDate.parse(date).plusDays(days).atStartOfDay(java.time.ZoneId.of("Asia/Tokyo")).toInstant().toString();
  }
}
