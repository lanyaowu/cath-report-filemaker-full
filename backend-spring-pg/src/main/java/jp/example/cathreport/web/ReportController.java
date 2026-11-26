package jp.example.cathreport.web;

import jakarta.validation.Valid;
import java.util.List;
import java.util.Objects;
import jp.example.cathreport.api.CathReport;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import jp.example.cathreport.audit.AuditDiff;
import jp.example.cathreport.audit.AuditService;
import jp.example.cathreport.security.Permission;
import jp.example.cathreport.security.AuthContext;
import jp.example.cathreport.service.ReportService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/reports")
public class ReportController {
  private final ReportService service;
  private final AuditService audit;
  private final ObjectMapper om;

  public ReportController(ReportService service, AuditService audit, ObjectMapper om) {
    this.service = service;
    this.audit = audit;
    this.om = om;
  }

  @GetMapping
  public List<CathReport> list(
      @RequestParam(required = false) String from,
      @RequestParam(required = false) String to,
      @RequestParam(required = false) String patientRef,
      @RequestParam(required = false) String status,
      @RequestParam(defaultValue = "5000") int limit) {
    return service.list(from, to, patientRef, status, limit);
  }

  @GetMapping("/{id}")
  public CathReport get(@PathVariable String id) {
    CathReport r = service.get(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    audit.record("VIEW_REPORT", "report", id, "");
    return r;
  }

  @PostMapping
  public CathReport create(@Valid @RequestBody CathReport r) {
    if (r.id == null || r.id.isBlank()) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "id が必要です");
    return save(r.id, r);
  }

  /** 登録・更新（業務ルール・楽観ロックは ReportService.saveAs で検査） */
  @PutMapping("/{id}")
  public CathReport save(@PathVariable String id, @Valid @RequestBody CathReport r) {
    CathReport before = service.getWithoutImageData(id).orElse(null);
    CathReport saved = service.saveAs(AuthContext.required(), id, r);
    // 変わった項目（画像本体 dataUrl は比べない）
    audit.record(before == null ? "CREATE_REPORT" : "UPDATE_REPORT", "report", id, changes(before, saved),
        AuditDiff.diff(before == null ? null : om.valueToTree(before), om.valueToTree(saved)));
    return saved;
  }

  /** レポートの変更履歴（そのレポートと患者。変わった項目つき。閲覧の権限） */
  @GetMapping("/{id}/history")
  public List<Map<String, Object>> history(@PathVariable String id) {
    AuthContext.require(Permission.READ);
    CathReport r = service.getWithoutImageData(id).orElse(null);
    return audit.reportHistory(id, r == null ? null : r.patientRef);
  }

  @DeleteMapping("/{id}")
  public ResponseEntity<Void> delete(@PathVariable String id) {
    if (service.deleteAs(AuthContext.required(), id)) audit.record("DELETE_REPORT", "report", id, "");
    return ResponseEntity.noContent().build();
  }

  /** 監査ログ用：ステータス・照合の変更 */
  static String changes(CathReport before, CathReport after) {
    StringBuilder b = new StringBuilder();
    String s0 = before == null ? "-" : before.status;
    if (!Objects.equals(s0, after.status)) b.append("status:").append(s0).append("→").append(after.status);
    boolean v0 = before != null && Boolean.TRUE.equals(before.verified);
    if (v0 != Boolean.TRUE.equals(after.verified)) b.append(b.length() > 0 ? " " : "").append("verified:").append(Boolean.TRUE.equals(after.verified));
    return b.toString();
  }
}
