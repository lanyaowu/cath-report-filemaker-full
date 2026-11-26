package jp.example.cathreport.repository;

import jp.example.cathreport.model.CathReport;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface CathReportRepository extends MongoRepository<CathReport, String> {
  long countByPatientRef(String patientRef);
}
