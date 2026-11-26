package jp.example.cathreport.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Map;
import jp.example.cathreport.model.CathReport;
import jp.example.cathreport.model.Masters;
import jp.example.cathreport.model.Patient;
import jp.example.cathreport.repository.CathReportRepository;
import jp.example.cathreport.repository.MastersRepository;
import jp.example.cathreport.repository.PatientRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

/** サンプルデータ投入（classpath:sample-data/*.json）。起動時は DB が空の場合のみ投入 */
@Service
public class SampleDataService implements ApplicationRunner {
  private static final Logger log = LoggerFactory.getLogger(SampleDataService.class);

  private final PatientRepository patients;
  private final CathReportRepository reports;
  private final MastersRepository masters;
  private final ObjectMapper mapper;
  private final boolean seedOnStartup;

  public SampleDataService(PatientRepository patients, CathReportRepository reports, MastersRepository masters, ObjectMapper mapper,
      @Value("${app.seed-on-startup:true}") boolean seedOnStartup) {
    this.patients = patients;
    this.reports = reports;
    this.masters = masters;
    this.mapper = mapper;
    this.seedOnStartup = seedOnStartup;
  }

  @Override
  public void run(ApplicationArguments args) throws IOException {
    if (seedOnStartup && patients.count() == 0) {
      Map<String, Integer> r = seed();
      log.info("サンプルデータを投入しました: {}", r);
    }
  }

  public Map<String, Integer> seed() throws IOException {
    List<Patient> ps = read("sample-data/patients.json", new TypeReference<>() {});
    List<CathReport> rs = read("sample-data/reports.json", new TypeReference<>() {});
    Masters m = read("sample-data/masters.json", new TypeReference<>() {});
    reports.deleteAll();
    patients.deleteAll();
    masters.deleteAll();
    patients.saveAll(ps);
    reports.saveAll(rs);
    m.id = Masters.DEFAULT_ID;
    masters.save(m);
    return Map.of("patients", ps.size(), "reports", rs.size());
  }

  private <T> T read(String path, TypeReference<T> type) throws IOException {
    try (InputStream in = new ClassPathResource(path).getInputStream()) {
      return mapper.readValue(in, type);
    }
  }
}
