package jp.example.cathreport.service;

import jakarta.persistence.criteria.Predicate;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import jp.example.cathreport.api.CathReport;
import jp.example.cathreport.entity.CathReportEntity;
import jp.example.cathreport.repository.CathReportRepository;
import jp.example.cathreport.repository.ImageDataDao;
import jp.example.cathreport.repository.PatientRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.HashMap;
import java.util.Map;
import jp.example.cathreport.security.AuthUser;
import jp.example.cathreport.security.Permission;
import jp.example.cathreport.security.ReportRules;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class ReportService {
  static final Set<String> STATUSES = Set.of("入力中", "確定");
  static final int MAX_LIMIT = 5000;

  private final CathReportRepository reports;
  private final PatientRepository patients;
  private final ImageDataDao images;
  private final ObjectMapper mapper;

  public ReportService(CathReportRepository reports, PatientRepository patients, ImageDataDao images, ObjectMapper mapper) {
    this.reports = reports;
    this.patients = patients;
    this.images = images;
    this.mapper = mapper;
  }

  /**
   * 利用者による登録・更新（API）。業務ルール（権限・確定ロック・登録履歴）を検査し、更新時は version を必須とする。
   * 比較は、保存済みと送られた内容を同じ変換（Entity → DTO）にかけてから行う。
   */
  @Transactional
  public CathReport saveAs(AuthUser user, String id, CathReport d) {
    // 権限 → 楽観ロック（他の端末の更新を先に知らせる）→ 業務ルール（確定ロック・履歴）
    ReportRules.require(user, Permission.EDIT);
    CathReportEntity e = reports.findById(id).orElse(null);
    if (e != null) ReportRules.nextVersion("レポート", true, e.version, d.version);
    Map<String, String> oldData = e == null ? Map.of() : images.load(id);
    JsonNode oldTree = e == null ? null : mapper.valueToTree(EntityMapper.toDto(e, oldData));
    CathReportEntity fresh = new CathReportEntity();
    fresh.id = id;
    EntityMapper.apply(d, fresh); // 日付の形式などもここで検査（400）
    Map<String, String> newData = new HashMap<>();
    if (d.images != null) {
      for (CathReport.Image i : d.images) {
        if (i == null || i.id == null) continue;
        // dataUrl の無い画像は保存済みの本体を維持する（ImageDataDao.sync と同じ扱い）
        newData.put(i.id, i.dataUrl == null || i.dataUrl.isBlank() ? oldData.get(i.id) : i.dataUrl);
      }
    }
    ReportRules.check(user, oldTree, mapper.valueToTree(EntityMapper.toDto(fresh, newData)));
    stampHistory(user, e == null ? 0 : e.history.size(), d);
    return save(id, d);
  }

  /** 今回追加された履歴の記録者をログイン中の利用者にする（追加がなければ1件追加） */
  static void stampHistory(AuthUser user, int oldLength, CathReport d) {
    List<CathReport.History> h = d.history == null ? new ArrayList<>() : new ArrayList<>(d.history);
    if (h.size() <= oldLength) {
      CathReport.History x = new CathReport.History();
      x.at = Instant.now().toString();
      x.action = oldLength == 0 ? "新規作成" : "保存";
      h.add(x);
    }
    for (int i = oldLength; i < h.size(); i++) {
      if (h.get(i) == null) h.set(i, new CathReport.History());
      h.get(i).by = user.displayName();
    }
    d.history = h;
  }

  /** 利用者による削除（確定済みは不可）。削除したら true */
  @Transactional
  public boolean deleteAs(AuthUser user, String id) {
    ReportRules.require(user, Permission.DELETE_REPORT);
    CathReportEntity e = reports.findById(id).orElse(null);
    if (e == null) return false;
    if (ReportRules.LOCKED.equals(e.status)) {
      throw new ResponseStatusException(HttpStatus.CONFLICT, "確定済みのレポートは削除できません（ステータスを「入力中」に戻してください）");
    }
    reports.deleteById(id);
    return true;
  }

  /** 一覧（施行日降順）。画像本体（report_image_data）は読まない */
  @Transactional(readOnly = true)
  public List<CathReport> list(String from, String to, String patientRef, String status, int limit) {
    var fromDate = Conv.date(from, "from");
    var toDate = Conv.date(to, "to");
    Specification<CathReportEntity> spec = (root, q, cb) -> {
      List<Predicate> p = new ArrayList<>();
      var studyDate = root.get("header").<java.time.LocalDate>get("studyDate");
      if (fromDate != null) p.add(cb.greaterThanOrEqualTo(studyDate, fromDate));
      if (toDate != null) p.add(cb.lessThanOrEqualTo(studyDate, toDate));
      if (patientRef != null && !patientRef.isBlank()) p.add(cb.equal(root.get("patientRef"), patientRef));
      if (status != null && !status.isBlank()) p.add(cb.equal(root.get("status"), status));
      return cb.and(p.toArray(Predicate[]::new));
    };
    Sort sort = Sort.by(Sort.Order.desc("header.studyDate"), Sort.Order.desc("updatedAt"));
    int n = Math.max(1, Math.min(limit, MAX_LIMIT));
    return reports.findBy(spec, f -> f.sortBy(sort).limit(n).all()).stream()
        .map(e -> EntityMapper.toDto(e, null))
        .toList();
  }

  /** 1件取得（画像本体を含まない） */
  @Transactional(readOnly = true)
  public Optional<CathReport> getWithoutImageData(String id) {
    return reports.findById(id).map(e -> EntityMapper.toDto(e, null));
  }

  /** 1件取得（画像本体を含む） */
  @Transactional(readOnly = true)
  public Optional<CathReport> get(String id) {
    return reports.findById(id).map(e -> EntityMapper.toDto(e, images.load(id)));
  }

  /** 登録/更新（レポート単位の全体置換）。version が送られた場合は不一致で 409 */
  @Transactional
  public CathReport save(String id, CathReport d) {
    if (d.patientRef == null || !patients.existsById(d.patientRef)) {
      throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "患者が存在しません（patientRef）");
    }
    if (d.status != null && !STATUSES.contains(d.status)) {
      throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "status は 入力中 / 確定 のいずれかです");
    }
    CathReportEntity e = reports.findById(id).orElse(null);
    if (e != null && d.version != null && !Objects.equals(d.version, e.version)) {
      throw new ResponseStatusException(HttpStatus.CONFLICT, "このレポートは他の端末で更新されています。再読み込みしてください");
    }
    Instant now = Instant.now();
    if (e == null) {
      e = new CathReportEntity();
      e.id = id;
      e.createdAt = Optional.ofNullable(Conv.instant(d.createdAt, "createdAt")).orElse(now);
    }
    EntityMapper.apply(d, e);
    e.updatedAt = now;
    CathReportEntity saved = reports.saveAndFlush(e); // 画像本体の外部キーのため先に確定
    images.sync(id, d.images == null ? List.of() : d.images);
    return EntityMapper.toDto(saved, images.load(id));
  }

  @Transactional
  public void delete(String id) {
    if (reports.existsById(id)) reports.deleteById(id); // 子テーブルは ON DELETE CASCADE
  }
}
