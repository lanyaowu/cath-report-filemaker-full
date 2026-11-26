package jp.example.cathreport.repository;

import jp.example.cathreport.entity.CathReportEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface CathReportRepository extends JpaRepository<CathReportEntity, String>, JpaSpecificationExecutor<CathReportEntity> {
  long countByPatientRef(String patientRef);
}
