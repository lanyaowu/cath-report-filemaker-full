package jp.example.cathreport;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.InputStream;
import java.util.List;
import jp.example.cathreport.api.CathReport;
import jp.example.cathreport.api.Patient;
import jp.example.cathreport.entity.CathReportEntity;
import jp.example.cathreport.entity.PatientEntity;
import jp.example.cathreport.service.EntityMapper;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;

/** サンプル JSON → エンティティ → JSON の往復で内容が変わらないこと（DB 不要） */
class EntityMapperTest {
  private final ObjectMapper mapper = new ObjectMapper().configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

  private <T> T read(String path, TypeReference<T> t) throws Exception {
    try (InputStream in = new ClassPathResource(path).getInputStream()) {
      return mapper.readValue(in, t);
    }
  }

  @Test
  void patientsRoundTrip() throws Exception {
    List<Patient> ps = read("sample-data/patients.json", new TypeReference<>() {});
    assertThat(ps).hasSize(8);
    for (Patient p : ps) {
      PatientEntity e = new PatientEntity();
      e.id = p.id;
      EntityMapper.apply(p, e);
      Patient back = EntityMapper.toDto(e);
      assertThat(back.patientId).isEqualTo(p.patientId);
      assertThat(back.birthDate).isEqualTo(p.birthDate == null ? "" : p.birthDate);
      assertThat(back.admissions).hasSameSizeAs(p.admissions);
      assertThat(back.infection).isEqualTo(p.infection);
    }
  }

  @Test
  void reportsRoundTrip() throws Exception {
    List<Patient> ps = read("sample-data/patients.json", new TypeReference<>() {});
    List<CathReport> rs = read("sample-data/reports.json", new TypeReference<>() {});
    assertThat(rs).isNotEmpty();
    for (CathReport r : rs) {
      assertThat(ps.stream().anyMatch(p -> p.id.equals(r.patientRef))).isTrue();
      CathReportEntity e = new CathReportEntity();
      e.id = r.id;
      EntityMapper.apply(r, e);
      CathReport back = EntityMapper.toDto(e, null);
      assertThat(back.header.studyDate).isEqualTo(r.header.studyDate);
      assertThat(back.cathRecord).isEqualTo(r.cathRecord);
      assertThat(back.pci).isEqualTo(r.pci);
      assertThat(back.mace).isEqualTo(r.mace);
      assertThat(back.images).hasSameSizeAs(r.images);
      assertThat(back.images).allSatisfy(i -> assertThat(i.dataUrl).isNull()); // 一覧形式は画像本体なし
      assertThat(back.history).hasSameSizeAs(r.history);
    }
  }
}
