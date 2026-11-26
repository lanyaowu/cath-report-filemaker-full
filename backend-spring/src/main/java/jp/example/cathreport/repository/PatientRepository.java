package jp.example.cathreport.repository;

import java.util.Optional;
import jp.example.cathreport.model.Patient;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface PatientRepository extends MongoRepository<Patient, String> {
  Optional<Patient> findByPatientId(String patientId);
}
