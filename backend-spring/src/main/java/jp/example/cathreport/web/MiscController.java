package jp.example.cathreport.web;

import java.io.IOException;
import java.time.Instant;
import java.util.Map;
import jp.example.cathreport.audit.AuditService;
import jp.example.cathreport.model.Masters;
import jp.example.cathreport.repository.MastersRepository;
import jp.example.cathreport.security.AuthContext;
import jp.example.cathreport.security.Permission;
import jp.example.cathreport.service.SampleDataService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

/** ヘルスチェック・マスタ・管理（サンプル投入） */
@RestController
@RequestMapping("/api")
public class MiscController {
  private final MastersRepository masters;
  private final SampleDataService sample;
  private final AuditService audit;
  private final boolean allowSeedApi;

  public MiscController(MastersRepository masters, SampleDataService sample, AuditService audit, @Value("${app.allow-seed-api:false}") boolean allowSeedApi) {
    this.masters = masters;
    this.sample = sample;
    this.audit = audit;
    this.allowSeedApi = allowSeedApi;
  }

  @GetMapping("/health")
  public Map<String, String> health() {
    return Map.of("status", "ok", "backend", "spring-boot", "time", Instant.now().toString());
  }

  @GetMapping("/masters")
  public Masters getMasters() {
    return masters.findById(Masters.DEFAULT_ID).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
  }

  @PutMapping("/masters")
  public Masters saveMasters(@RequestBody Masters m) {
    AuthContext.require(Permission.MASTERS);
    m.id = Masters.DEFAULT_ID;
    Masters saved = masters.save(m);
    audit.record("UPDATE_MASTERS", "masters", Masters.DEFAULT_ID, "");
    return saved;
  }

  /** サンプルデータ投入（全データ置換）。管理者のみ、かつ ALLOW_SEED_API=true のときだけ */
  @PostMapping("/admin/seed")
  public Map<String, Integer> seed() throws IOException {
    AuthContext.require(Permission.SEED);
    if (!allowSeedApi) throw new ResponseStatusException(HttpStatus.FORBIDDEN, "サンプルデータの投入は無効です（サーバーの ALLOW_SEED_API=true で有効）");
    Map<String, Integer> r = sample.seed();
    audit.record("SEED", "all", "", r.toString());
    return r;
  }
}
