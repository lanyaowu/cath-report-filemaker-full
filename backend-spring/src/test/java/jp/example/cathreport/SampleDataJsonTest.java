package jp.example.cathreport;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.InputStream;
import java.util.List;
import jp.example.cathreport.model.CathReport;
import jp.example.cathreport.model.Patient;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;

/** サンプルJSONがエンティティへ正しくマッピングできることを確認（MongoDB 不要） */
class SampleDataJsonTest {
  private final ObjectMapper mapper = new ObjectMapper().configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

  @Test
  void patientsAndReportsDeserialize() throws Exception {
    try (InputStream p = new ClassPathResource("sample-data/patients.json").getInputStream();
        InputStream r = new ClassPathResource("sample-data/reports.json").getInputStream()) {
      List<Patient> ps = mapper.readValue(p, new TypeReference<>() {});
      List<CathReport> rs = mapper.readValue(r, new TypeReference<>() {});
      assertThat(ps).hasSize(8);
      assertThat(rs).isNotEmpty();
      assertThat(rs).allSatisfy(x -> assertThat(ps.stream().anyMatch(pt -> pt.id.equals(x.patientRef))).isTrue());
      assertThat(rs.get(0).header.studyDate).isNotBlank();
    }
  }
}
