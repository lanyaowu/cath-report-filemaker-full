package jp.example.cathreport.web;

import jakarta.validation.Valid;
import java.time.Instant;
import java.util.List;
import java.util.Locale;
import com.fasterxml.jackson.databind.ObjectMapper;
import jp.example.cathreport.audit.AuditDiff;
import jp.example.cathreport.audit.AuditService;
import jp.example.cathreport.model.Patient;
import jp.example.cathreport.repository.CathReportRepository;
import jp.example.cathreport.repository.PatientRepository;
import jp.example.cathreport.security.AuthContext;
import jp.example.cathreport.security.Permission;
import jp.example.cathreport.security.ReportRules;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/patients")
public class PatientController {
  private final PatientRepository patients;
  private final CathReportRepository reports;
  private final MongoTemplate mongo;
  private final AuditService audit;

  private final ObjectMapper om;

  public PatientController(PatientRepository patients, CathReportRepository reports, MongoTemplate mongo, AuditService audit, ObjectMapper om) {
    this.patients = patients;
    this.reports = reports;
    this.mongo = mongo;
    this.audit = audit;
    this.om = om;
  }

  @GetMapping
  public List<Patient> list(@RequestParam(required = false) String q) {
    List<Patient> all = patients.findAll(Sort.by("kana"));
    all.forEach(PatientController::defaultVersion);
    if (q == null || q.isBlank()) return all;
    String s = q.toLowerCase(Locale.ROOT);
    return all.stream()
        .filter(p -> String.join(" ", nz(p.patientId), nz(p.name), nz(p.kana)).toLowerCase(Locale.ROOT).contains(s))
        .toList();
  }

  @GetMapping("/{id}")
  public Patient get(@PathVariable String id) {
    Patient p = patients.findById(id).map(PatientController::defaultVersion).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    audit.record("VIEW_PATIENT", "patient", id, "");
    return p;
  }

  @PostMapping
  public Patient create(@Valid @RequestBody Patient p) {
    if (p.id == null || p.id.isBlank()) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "id が必要です");
    return upsert(p.id, p);
  }

  /** 登録・更新。患者ID の重複は 409、version 不一致・未指定（更新時）は 409 */
  @PutMapping("/{id}")
  public Patient upsert(@PathVariable String id, @Valid @RequestBody Patient p) {
    ReportRules.require(AuthContext.required(), Permission.EDIT);
    patients.findByPatientId(p.patientId).filter(x -> !x.id.equals(id)).ifPresent(x -> {
      throw new ResponseStatusException(HttpStatus.CONFLICT, "患者ID " + p.patientId + " は既に登録されています");
    });
    Patient old = patients.findById(id).orElse(null);
    long stored = old == null || old.version == null ? 0 : old.version;
    p.version = ReportRules.nextVersion("患者", old != null, stored, p.version);
    String now = Instant.now().toString();
    p.id = id;
    p.updatedAt = now;
    p.createdAt = old != null && old.createdAt != null ? old.createdAt : p.createdAt == null ? now : p.createdAt;
    if (old == null) {
      patients.insert(p);
    } else {
      Criteria v = stored == 0
          ? new Criteria().orOperator(Criteria.where("version").is(0L), Criteria.where("version").exists(false))
          : Criteria.where("version").is(stored);
      if (mongo.findAndReplace(new Query(new Criteria().andOperator(Criteria.where("_id").is(id), v)), p) == null) {
        throw new ResponseStatusException(HttpStatus.CONFLICT, "この患者は他の端末で更新されています。再読み込みしてください");
      }
    }
    audit.record(old == null ? "CREATE_PATIENT" : "UPDATE_PATIENT", "patient", id, "",
        AuditDiff.diff(old == null ? null : om.valueToTree(old), om.valueToTree(p)));
    return p;
  }

  @DeleteMapping("/{id}")
  public ResponseEntity<Void> delete(@PathVariable String id) {
    ReportRules.require(AuthContext.required(), Permission.DELETE_PATIENT);
    long n = reports.countByPatientRef(id);
    if (n > 0) throw new ResponseStatusException(HttpStatus.CONFLICT, "この患者には " + n + " 件のレポートがあるため削除できません");
    if (patients.existsById(id)) {
      patients.deleteById(id);
      audit.record("DELETE_PATIENT", "patient", id, "");
    }
    return ResponseEntity.noContent().build();
  }

  static Patient defaultVersion(Patient p) {
    if (p.version == null) p.version = 0L;
    return p;
  }

  private static String nz(String s) {
    return s == null ? "" : s;
  }
}
