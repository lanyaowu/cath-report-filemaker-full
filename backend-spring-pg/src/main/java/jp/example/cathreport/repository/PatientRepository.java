package jp.example.cathreport.repository;

import java.util.List;
import java.util.Optional;
import jp.example.cathreport.entity.PatientEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PatientRepository extends JpaRepository<PatientEntity, String> {
  Optional<PatientEntity> findByPatientId(String patientId);

  List<PatientEntity> findAllByOrderByKanaAscPatientIdAsc();

  /** 患者ID・氏名・フリガナの部分一致（pattern は小文字化・エスケープ済みの %...%） */
  @Query("""
      select p from PatientEntity p
      where lower(concat(coalesce(p.patientId, ''), ' ', coalesce(p.name, ''), ' ', coalesce(p.kana, ''))) like :pattern escape '\\'
      order by p.kana, p.patientId
      """)
  List<PatientEntity> search(@Param("pattern") String pattern);
}
