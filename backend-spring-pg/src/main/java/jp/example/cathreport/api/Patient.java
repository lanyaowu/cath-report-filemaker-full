package jp.example.cathreport.api;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.NotBlank;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 患者（API の JSON 形式）。フロントエンド types/model.ts の Patient と1対1で対応し、
 * MongoDB 版と同じ形式。DB への保存は entity.PatientEntity（列＋JSONB）に変換して行う。
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class Patient {
  public String id;
  @NotBlank public String patientId;
  @NotBlank public String name;
  public String kana;
  public String sex;
  public String birthDate;
  public String bloodType;
  public String rh;
  public String zip;
  public String address;
  public String phone;
  public String mobile;
  /** name, relation, phone */
  public Map<String, Object> emergency;
  /** type, number */
  public Map<String, Object> insurance;
  /** contrast, contrastDetail, drug, drugDetail, latex, iodine, food */
  public Map<String, Object> allergy;
  /** hbs, hcv, hiv, syphilis, mrsa */
  public Map<String, Object> infection;
  public String primaryDoctor;
  public String ward;
  /** hospital, doctor */
  public Map<String, Object> referral;
  public Boolean dnar;
  public String pastHistory;
  public String familyHistory;
  public String medicationNote;
  public String notes;
  /** 病歴総括 */
  public List<Admission> admissions = new ArrayList<>();
  public String createdAt;
  public String updatedAt;
  /** 楽観ロック用（任意）。送られた場合のみ DB の値と照合し、不一致なら 409 */
  public Long version;

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class Admission {
    public String admitDate;
    public String dischargeDate;
    public String doctor;
    public String diagnosis;
    public String summary;
  }
}
