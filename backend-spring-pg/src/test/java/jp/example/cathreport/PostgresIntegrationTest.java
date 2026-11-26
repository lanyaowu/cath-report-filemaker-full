package jp.example.cathreport;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;
import java.util.Map;
import jp.example.cathreport.api.CathReport;
import jp.example.cathreport.service.PatientService;
import jp.example.cathreport.service.ReportService;
import jp.example.cathreport.service.SampleDataService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.server.ResponseStatusException;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

/** 実 PostgreSQL（Testcontainers）での結合テスト。Docker が無い環境では自動的にスキップ */
@SpringBootTest(properties = "app.seed-on-startup=false")
@Testcontainers(disabledWithoutDocker = true)
class PostgresIntegrationTest {
  @Container @ServiceConnection
  static PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:16-alpine");

  @Autowired SampleDataService sample;
  @Autowired ReportService reports;
  @Autowired PatientService patients;
  @Autowired JdbcTemplate jdbc;

  @Test
  void seedListGetSave() throws Exception {
    Map<String, Integer> r = sample.seed();
    assertThat(r.get("patients")).isEqualTo(8);

    List<CathReport> list = reports.list(null, null, null, null, 100);
    assertThat(list).hasSize(r.get("reports"));
    assertThat(list).allSatisfy(x -> x.images.forEach(i -> assertThat(i.dataUrl).isNull()));

    CathReport withImages = list.stream().filter(x -> !x.images.isEmpty()).findFirst().orElseThrow();
    CathReport full = reports.get(withImages.id).orElseThrow();
    assertThat(full.images.get(0).dataUrl).startsWith("data:");

    // 画像を1枚外して保存 → 本体も削除される
    full.images.remove(0);
    CathReport saved = reports.save(full.id, full);
    assertThat(saved.version).isGreaterThan(full.version);
    Integer n = jdbc.queryForObject("SELECT count(*) FROM report_image_data WHERE report_id = ?", Integer.class, full.id);
    assertThat(n).isEqualTo(full.images.size());

    // 古い version での保存は 409
    assertThatThrownBy(() -> reports.save(full.id, full)).isInstanceOf(ResponseStatusException.class);

    // レポートのある患者は削除不可
    assertThatThrownBy(() -> patients.delete(full.patientRef)).isInstanceOf(ResponseStatusException.class);

    assertThat(jdbc.queryForList("SELECT * FROM v_report_summary")).hasSize(r.get("reports"));
  }
}
