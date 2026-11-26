package jp.example.cathreport.web;

import jp.example.cathreport.audit.AuditService;
import jp.example.cathreport.security.AuthContext;
import jp.example.cathreport.security.Permission;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import jp.example.cathreport.api.Masters;
import jp.example.cathreport.service.MastersService;
import jp.example.cathreport.service.SampleDataService;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

/** ヘルスチェック・マスタ・管理（サンプル投入）・集計ビュー */
@RestController
@RequestMapping("/api")
public class MiscController {
  private final MastersService masters;
  private final SampleDataService sample;
  private final JdbcTemplate jdbc;
  private final AuditService audit;
  private final boolean allowSeedApi;

  public MiscController(MastersService masters, SampleDataService sample, JdbcTemplate jdbc, AuditService audit,
      @Value("${app.allow-seed-api:false}") boolean allowSeedApi) {
    this.masters = masters;
    this.sample = sample;
    this.jdbc = jdbc;
    this.audit = audit;
    this.allowSeedApi = allowSeedApi;
  }

  @GetMapping("/health")
  public Map<String, String> health() {
    Map<String, String> m = new LinkedHashMap<>();
    m.put("status", "ok");
    m.put("backend", "spring-boot-postgresql");
    m.put("db", jdbc.queryForObject("SELECT current_setting('server_version')", String.class));
    m.put("time", Instant.now().toString());
    return m;
  }

  @GetMapping("/masters")
  public Masters getMasters() {
    return masters.get();
  }

  @PutMapping("/masters")
  public Masters saveMasters(@RequestBody Masters m) {
    AuthContext.require(Permission.MASTERS);
    Masters saved = masters.save(m);
    audit.record("UPDATE_MASTERS", "masters", "default", "");
    return saved;
  }

  @PostMapping("/admin/seed")
  public Map<String, Integer> seed() throws IOException {
    AuthContext.require(Permission.SEED);
    if (!allowSeedApi) throw new ResponseStatusException(HttpStatus.FORBIDDEN, "サンプルデータの投入は無効です（サーバーの ALLOW_SEED_API=true で有効）");
    Map<String, Integer> r = sample.seed();
    audit.record("SEED", "all", "", r.toString());
    return r;
  }

  /** 月別件数（v_monthly_stats）— PostgreSQL 版のみ */
  @GetMapping("/stats/monthly")
  public List<Map<String, Object>> monthly() {
    return jdbc.queryForList("SELECT * FROM v_monthly_stats ORDER BY month DESC");
  }

  /** MACE 追跡一覧（v_mace_events）— PostgreSQL 版のみ */
  @GetMapping("/stats/mace")
  public List<Map<String, Object>> mace() {
    return jdbc.queryForList("SELECT * FROM v_mace_events ORDER BY study_date DESC, mace_no");
  }
}
