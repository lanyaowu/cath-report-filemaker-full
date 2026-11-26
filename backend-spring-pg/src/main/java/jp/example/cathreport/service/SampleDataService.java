package jp.example.cathreport.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.EntityManager;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Map;
import jp.example.cathreport.api.CathReport;
import jp.example.cathreport.api.Masters;
import jp.example.cathreport.api.Patient;
import jp.example.cathreport.repository.PatientRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

/** サンプルデータ投入（classpath:sample-data/*.json）。起動時は DB が空の場合のみ投入 */
@Service
public class SampleDataService implements ApplicationRunner {
  private static final Logger log = LoggerFactory.getLogger(SampleDataService.class);

  private final PatientRepository patientRepo;
  private final PatientService patients;
  private final ReportService reports;
  private final MastersService masters;
  private final JdbcTemplate jdbc;
  private final EntityManager em;
  private final ObjectMapper mapper;
  private final TransactionTemplate tx;
  private final boolean seedOnStartup;

  public SampleDataService(PatientRepository patientRepo, PatientService patients, ReportService reports, MastersService masters,
      JdbcTemplate jdbc, EntityManager em, ObjectMapper mapper, TransactionTemplate tx, @Value("${app.seed-on-startup:true}") boolean seedOnStartup) {
    this.patientRepo = patientRepo;
    this.patients = patients;
    this.reports = reports;
    this.masters = masters;
    this.jdbc = jdbc;
    this.em = em;
    this.mapper = mapper;
    this.tx = tx;
    this.seedOnStartup = seedOnStartup;
  }

  @Override
  public void run(ApplicationArguments args) throws IOException {
    if (seedOnStartup && patientRepo.count() == 0) {
      Map<String, Integer> r = seed();
      log.info("サンプルデータを投入しました: {}", r);
    }
  }

  /** 全データを削除してサンプルを投入（POST /api/admin/seed）。1トランザクションで実行 */
  public Map<String, Integer> seed() throws IOException {
    List<Patient> ps = read("sample-data/patients.json", new TypeReference<>() {});
    List<CathReport> rs = read("sample-data/reports.json", new TypeReference<>() {});
    Masters m = read("sample-data/masters.json", new TypeReference<>() {});
    return tx.execute(status -> replaceAll(ps, rs, m));
  }

  private Map<String, Integer> replaceAll(List<Patient> ps, List<CathReport> rs, Masters m) {
    em.flush();
    em.clear();
    jdbc.execute("TRUNCATE report_image_data, report_images, report_mace, report_history, cath_reports,"
        + " patient_admissions, patients, master_items RESTART IDENTITY");
    for (Patient p : ps) {
      p.version = null;
      patients.save(p.id, p);
    }
    int images = 0;
    for (CathReport r : rs) {
      r.version = null;
      reports.save(r.id, r);
      images += r.images == null ? 0 : r.images.size();
    }
    masters.save(m);
    return Map.of("patients", ps.size(), "reports", rs.size(), "images", images);
  }

  private <T> T read(String path, TypeReference<T> type) throws IOException {
    try (InputStream in = new ClassPathResource(path).getInputStream()) {
      return mapper.readValue(in, type);
    }
  }
}
