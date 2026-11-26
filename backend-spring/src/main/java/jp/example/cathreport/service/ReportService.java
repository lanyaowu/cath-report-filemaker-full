package jp.example.cathreport.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import jp.example.cathreport.model.CathReport;
import jp.example.cathreport.repository.CathReportRepository;
import jp.example.cathreport.repository.PatientRepository;
import jp.example.cathreport.security.AuthUser;
import jp.example.cathreport.security.Permission;
import jp.example.cathreport.security.ReportRules;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class ReportService {
  private final CathReportRepository reports;
  private final PatientRepository patients;
  private final MongoTemplate mongo;
  private final ObjectMapper mapper;

  public ReportService(CathReportRepository reports, PatientRepository patients, MongoTemplate mongo, ObjectMapper mapper) {
    this.reports = reports;
    this.patients = patients;
    this.mongo = mongo;
    this.mapper = mapper;
  }

  /** 一覧（画像本体 images.dataUrl を除外したプロジェクション） */
  public List<CathReport> list(String from, String to, String patientRef, String status, int limit) {
    Query q = new Query();
    if (from != null || to != null) {
      Criteria c = Criteria.where("header.studyDate");
      if (from != null) c = c.gte(from);
      if (to != null) c = c.lte(to);
      q.addCriteria(c);
    }
    if (patientRef != null) q.addCriteria(Criteria.where("patientRef").is(patientRef));
    if (status != null) q.addCriteria(Criteria.where("status").is(status));
    q.fields().exclude("images.dataUrl");
    q.with(Sort.by(Sort.Direction.DESC, "header.studyDate")).limit(limit);
    List<CathReport> list = mongo.find(q, CathReport.class);
    list.forEach(ReportService::defaultVersion);
    return list;
  }

  public Optional<CathReport> get(String id) {
    return reports.findById(id).map(ReportService::defaultVersion);
  }

  /** 保存前のデータには version が無いので 0 とみなす */
  static CathReport defaultVersion(CathReport r) {
    if (r.version == null) r.version = 0L;
    return r;
  }

  /**
   * 登録・更新（API）。業務ルール（権限・確定ロック・登録履歴）と楽観ロックを検査し、
   * version が保存時と同じ場合だけ置き換える。
   */
  public CathReport save(AuthUser user, String id, CathReport r) {
    if (!patients.existsById(r.patientRef)) {
      throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "患者が存在しません（patientRef）");
    }
    CathReport old = reports.findById(id).orElse(null);
    r.id = id;
    if (r.status == null) r.status = "入力中";
    if (r.verified == null) r.verified = false;
    // 権限 → 楽観ロック（他の端末の更新を先に知らせる）→ 業務ルール（確定ロック・履歴）
    ReportRules.require(user, Permission.EDIT);
    long stored = old == null || old.version == null ? 0 : old.version;
    long next = ReportRules.nextVersion("レポート", old != null, stored, r.version);
    JsonNode oldTree = old == null ? null : mapper.valueToTree(old);
    ReportRules.check(user, oldTree, mapper.valueToTree(r));
    r.version = next;
    stampHistory(user, old == null || old.history == null ? 0 : old.history.size(), r);
    String now = Instant.now().toString();
    r.updatedAt = now;
    r.createdAt = old != null && old.createdAt != null ? old.createdAt : r.createdAt == null ? now : r.createdAt;
    if (old == null) return reports.insert(r);
    Criteria v = stored == 0
        ? new Criteria().orOperator(Criteria.where("version").is(0L), Criteria.where("version").exists(false))
        : Criteria.where("version").is(stored);
    Query q = new Query(new Criteria().andOperator(Criteria.where("_id").is(id), v));
    if (mongo.findAndReplace(q, r) == null) {
      throw new ResponseStatusException(HttpStatus.CONFLICT, "このレポートは他の端末で更新されています。再読み込みしてください");
    }
    return r;
  }

  /** 今回追加された履歴の記録者をログイン中の利用者にする（追加がなければ1件追加） */
  static void stampHistory(AuthUser user, int oldLength, CathReport r) {
    List<Map<String, Object>> h = r.history == null ? new ArrayList<>() : new ArrayList<>(r.history);
    if (h.size() <= oldLength) {
      Map<String, Object> e = new LinkedHashMap<>();
      e.put("at", Instant.now().toString());
      e.put("by", user.displayName());
      e.put("action", oldLength == 0 ? "新規作成" : "保存");
      h.add(e);
    }
    for (int i = oldLength; i < h.size(); i++) {
      Map<String, Object> e = new LinkedHashMap<>(h.get(i) == null ? Map.of() : h.get(i));
      e.put("by", user.displayName());
      h.set(i, e);
    }
    r.history = h;
  }

  /** 削除（確定済みは不可） */
  public boolean delete(AuthUser user, String id) {
    ReportRules.require(user, Permission.DELETE_REPORT);
    CathReport r = reports.findById(id).orElse(null);
    if (r == null) return false;
    if (ReportRules.LOCKED.equals(r.status)) {
      throw new ResponseStatusException(HttpStatus.CONFLICT, "確定済みのレポートは削除できません（ステータスを「入力中」に戻してください）");
    }
    reports.deleteById(id);
    return true;
  }
}
