package jp.example.cathreport.entity;

import jakarta.persistence.*;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/** 患者（table: patients）。列名は Spring Boot 既定の命名規則（camelCase → snake_case） */
@Entity
@Table(name = "patients")
public class PatientEntity {
  @Id public String id;
  public String patientId;
  public String name;
  public String kana;
  public String sex;
  public LocalDate birthDate;
  public String bloodType;
  public String rh;
  public String zip;
  public String address;
  public String phone;
  public String mobile;

  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> emergency;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> insurance;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> allergy;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> infection;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> referral;

  public String primaryDoctor;
  public String ward;
  public boolean dnar;
  public String pastHistory;
  public String familyHistory;
  public String medicationNote;
  public String notes;

  /** 病歴総括（patient_admissions） */
  @ElementCollection
  @CollectionTable(name = "patient_admissions", joinColumns = @JoinColumn(name = "patient_id"))
  @OrderColumn(name = "seq")
  public List<AdmissionEmb> admissions = new ArrayList<>();

  public Instant createdAt;
  public Instant updatedAt;
  @Version public Long version;

  @Embeddable
  public static class AdmissionEmb {
    public LocalDate admitDate;
    public LocalDate dischargeDate;
    public String doctor;
    public String diagnosis;
    public String summary;
  }
}
