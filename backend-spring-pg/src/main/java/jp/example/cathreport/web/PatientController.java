package jp.example.cathreport.web;

import jakarta.validation.Valid;
import java.util.List;
import jp.example.cathreport.api.Patient;
import com.fasterxml.jackson.databind.ObjectMapper;
import jp.example.cathreport.audit.AuditDiff;
import jp.example.cathreport.audit.AuditService;
import jp.example.cathreport.security.AuthContext;
import jp.example.cathreport.service.PatientService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/patients")
public class PatientController {
  private final PatientService service;
  private final AuditService audit;
  private final ObjectMapper om;

  public PatientController(PatientService service, AuditService audit, ObjectMapper om) {
    this.service = service;
    this.audit = audit;
    this.om = om;
  }

  @GetMapping
  public List<Patient> list(@RequestParam(required = false) String q) {
    return service.list(q);
  }

  @GetMapping("/{id}")
  public Patient get(@PathVariable String id) {
    Patient p = service.get(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    audit.record("VIEW_PATIENT", "patient", id, "");
    return p;
  }

  @PostMapping
  public Patient create(@Valid @RequestBody Patient p) {
    if (p.id == null || p.id.isBlank()) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "id が必要です");
    return upsert(p.id, p);
  }

  /** 登録・更新。患者ID の重複は 409、更新時の version 不一致・未指定は 409 */
  @PutMapping("/{id}")
  public Patient upsert(@PathVariable String id, @Valid @RequestBody Patient p) {
    Patient before = service.get(id).orElse(null);
    Patient saved = service.saveAs(AuthContext.required(), id, p);
    audit.record(before != null ? "UPDATE_PATIENT" : "CREATE_PATIENT", "patient", id, "",
        AuditDiff.diff(before == null ? null : om.valueToTree(before), om.valueToTree(saved)));
    return saved;
  }

  @DeleteMapping("/{id}")
  public ResponseEntity<Void> delete(@PathVariable String id) {
    if (service.deleteAs(AuthContext.required(), id)) audit.record("DELETE_PATIENT", "patient", id, "");
    return ResponseEntity.noContent().build();
  }
}
