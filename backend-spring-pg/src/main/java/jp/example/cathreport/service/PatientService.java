package jp.example.cathreport.service;

import java.time.Instant;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import jp.example.cathreport.api.Patient;
import jp.example.cathreport.entity.PatientEntity;
import jp.example.cathreport.repository.CathReportRepository;
import jp.example.cathreport.repository.PatientRepository;
import jp.example.cathreport.security.AuthUser;
import jp.example.cathreport.security.Permission;
import jp.example.cathreport.security.ReportRules;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class PatientService {
  private final PatientRepository patients;
  private final CathReportRepository reports;

  public PatientService(PatientRepository patients, CathReportRepository reports) {
    this.patients = patients;
    this.reports = reports;
  }

  @Transactional(readOnly = true)
  public List<Patient> list(String q) {
    List<PatientEntity> rows = q == null || q.isBlank()
        ? patients.findAllByOrderByKanaAscPatientIdAsc()
        : patients.search("%" + escapeLike(q.trim().toLowerCase(Locale.ROOT)) + "%");
    return rows.stream().map(EntityMapper::toDto).toList();
  }

  @Transactional(readOnly = true)
  public Optional<Patient> get(String id) {
    return patients.findById(id).map(EntityMapper::toDto);
  }

  /** 利用者による登録・更新（API）。編集権限と、更新時の version を必須とする */
  @Transactional
  public Patient saveAs(AuthUser user, String id, Patient d) {
    ReportRules.require(user, Permission.EDIT);
    PatientEntity e = patients.findById(id).orElse(null);
    if (e != null) ReportRules.nextVersion("患者", true, e.version, d.version);
    return save(id, d);
  }

  /** 利用者による削除。削除したら true */
  @Transactional
  public boolean deleteAs(AuthUser user, String id) {
    ReportRules.require(user, Permission.DELETE_PATIENT);
    boolean exists = patients.existsById(id);
    delete(id);
    return exists;
  }

  /** 登録/更新（upsert）。患者ID の重複は 409、version 不一致は 409 */
  @Transactional
  public Patient save(String id, Patient d) {
    patients.findByPatientId(d.patientId == null ? null : d.patientId.trim()).filter(x -> !x.id.equals(id)).ifPresent(x -> {
      throw new ResponseStatusException(HttpStatus.CONFLICT, "患者ID " + d.patientId + " は既に登録されています");
    });
    PatientEntity e = patients.findById(id).orElse(null);
    if (e != null && d.version != null && !Objects.equals(d.version, e.version)) {
      throw new ResponseStatusException(HttpStatus.CONFLICT, "この患者は他の端末で更新されています。再読み込みしてください");
    }
    Instant now = Instant.now();
    if (e == null) {
      e = new PatientEntity();
      e.id = id;
      e.createdAt = Optional.ofNullable(Conv.instant(d.createdAt, "createdAt")).orElse(now);
    }
    EntityMapper.apply(d, e);
    e.updatedAt = now;
    return EntityMapper.toDto(patients.saveAndFlush(e));
  }

  @Transactional
  public void delete(String id) {
    long n = reports.countByPatientRef(id);
    if (n > 0) throw new ResponseStatusException(HttpStatus.CONFLICT, "この患者には " + n + " 件のレポートがあるため削除できません");
    if (patients.existsById(id)) patients.deleteById(id);
  }

  static String escapeLike(String s) {
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_");
  }
}
