package jp.example.cathreport.service;

import static jp.example.cathreport.service.Conv.*;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import jp.example.cathreport.api.CathReport;
import jp.example.cathreport.api.Patient;
import jp.example.cathreport.api.ReportHeader;
import jp.example.cathreport.entity.CathReportEntity;
import jp.example.cathreport.entity.CathReportEntity.HeaderEmb;
import jp.example.cathreport.entity.CathReportEntity.HistoryEmb;
import jp.example.cathreport.entity.CathReportEntity.ImageEmb;
import jp.example.cathreport.entity.CathReportEntity.MaceEmb;
import jp.example.cathreport.entity.PatientEntity;
import jp.example.cathreport.entity.PatientEntity.AdmissionEmb;

/** API 形式（JSON）⇔ エンティティ（列＋JSONB）の変換。JSON の形は MongoDB 版と同一 */
public final class EntityMapper {
  private EntityMapper() {}

  /** MACE 画面のイベント項目（data 内のキー → 展開列） */
  static final List<String> MACE_EVENTS = List.of("death", "acs", "stroke", "hf", "bleeding", "revasc", "other");

  // ===================== 患者 =====================

  public static void apply(Patient d, PatientEntity e) {
    e.patientId = d.patientId == null ? null : d.patientId.trim();
    e.name = d.name;
    e.kana = d.kana;
    e.sex = d.sex;
    e.birthDate = date(d.birthDate, "birthDate");
    e.bloodType = d.bloodType;
    e.rh = d.rh;
    e.zip = d.zip;
    e.address = d.address;
    e.phone = d.phone;
    e.mobile = d.mobile;
    e.emergency = d.emergency;
    e.insurance = d.insurance;
    e.allergy = d.allergy;
    e.infection = d.infection;
    e.primaryDoctor = d.primaryDoctor;
    e.ward = d.ward;
    e.referral = d.referral;
    e.dnar = bool(d.dnar);
    e.pastHistory = d.pastHistory;
    e.familyHistory = d.familyHistory;
    e.medicationNote = d.medicationNote;
    e.notes = d.notes;
    e.admissions.clear();
    if (d.admissions != null) {
      for (Patient.Admission a : d.admissions) {
        if (a == null) continue;
        AdmissionEmb x = new AdmissionEmb();
        x.admitDate = date(a.admitDate, "admissions.admitDate");
        x.dischargeDate = date(a.dischargeDate, "admissions.dischargeDate");
        x.doctor = a.doctor;
        x.diagnosis = a.diagnosis;
        x.summary = a.summary;
        e.admissions.add(x);
      }
    }
  }

  public static Patient toDto(PatientEntity e) {
    Patient d = new Patient();
    d.id = e.id;
    d.patientId = e.patientId;
    d.name = e.name;
    d.kana = e.kana;
    d.sex = e.sex;
    d.birthDate = date(e.birthDate);
    d.bloodType = e.bloodType;
    d.rh = e.rh;
    d.zip = e.zip;
    d.address = e.address;
    d.phone = e.phone;
    d.mobile = e.mobile;
    d.emergency = e.emergency;
    d.insurance = e.insurance;
    d.allergy = e.allergy;
    d.infection = e.infection;
    d.primaryDoctor = e.primaryDoctor;
    d.ward = e.ward;
    d.referral = e.referral;
    d.dnar = e.dnar;
    d.pastHistory = e.pastHistory;
    d.familyHistory = e.familyHistory;
    d.medicationNote = e.medicationNote;
    d.notes = e.notes;
    d.admissions = new ArrayList<>();
    for (AdmissionEmb a : e.admissions) {
      Patient.Admission x = new Patient.Admission();
      x.admitDate = date(a.admitDate);
      x.dischargeDate = date(a.dischargeDate);
      x.doctor = a.doctor;
      x.diagnosis = a.diagnosis;
      x.summary = a.summary;
      d.admissions.add(x);
    }
    d.createdAt = instant(e.createdAt);
    d.updatedAt = instant(e.updatedAt);
    d.version = e.version;
    return d;
  }

  // ===================== レポート =====================

  public static void apply(CathReport d, CathReportEntity e) {
    e.patientRef = d.patientRef;
    e.status = d.status == null ? "入力中" : d.status;
    e.verified = bool(d.verified);

    ReportHeader h = d.header;
    HeaderEmb x = e.header == null ? (e.header = new HeaderEmb()) : e.header;
    x.studyDate = date(h.studyDate, "header.studyDate");
    x.cineNo = h.cineNo;
    x.pciNo = h.pciNo;
    x.accessionNo = h.accessionNo;
    x.secretaryChecked = bool(h.secretaryChecked);
    x.summary = bool(h.summary);
    x.submitted = bool(h.submitted);
    x.qca = bool(h.qca);
    x.registrant = h.registrant;

    e.cathRecord = d.cathRecord;
    e.cagLvg = d.cagLvg;
    e.pci = d.pci;
    e.pressureIvus = d.pressureIvus;
    e.pcps = d.pcps;
    e.conference = d.conference;
    e.restudy = d.restudy;

    e.history.clear();
    if (d.history != null) {
      for (CathReport.History hi : d.history) {
        if (hi == null) continue;
        HistoryEmb y = new HistoryEmb();
        y.at = instant(hi.at, "history.at");
        if (y.at == null) y.at = java.time.Instant.now();
        y.by = hi.by;
        y.action = hi.action;
        e.history.add(y);
      }
    }

    e.mace.clear();
    if (d.mace != null) for (Map<String, Object> m : d.mace) if (m != null) e.mace.add(toMace(m));

    e.images.clear();
    if (d.images != null) {
      for (CathReport.Image i : d.images) {
        if (i == null) continue;
        ImageEmb y = new ImageEmb();
        y.imageId = i.id;
        y.category = i.category;
        y.takenAt = date(i.takenAt, "images.takenAt");
        y.view = i.view;
        y.lesion = i.lesion;
        y.title = i.title;
        y.description = i.description;
        y.fileName = i.fileName;
        y.mimeType = i.mimeType;
        y.keyImage = bool(i.keyImage);
        e.images.add(y);
      }
    }
  }

  /** MACE の画面データを保持しつつ、集計用の列（イベント有無・最初のイベント日）を展開 */
  static MaceEmb toMace(Map<String, Object> m) {
    MaceEmb x = new MaceEmb();
    x.data = m;
    x.mace = str(m.get("mace"));
    x.pciDate = dateLenient(m.get("pciDate"));
    x.lastVisit = dateLenient(m.get("lastVisit"));
    LocalDate first = null;
    for (String ev : MACE_EVENTS) {
      Map<String, Object> o = map(m.get(ev));
      boolean on = truthy(o.get("checked"));
      switch (ev) {
        case "death" -> x.hasDeath = on;
        case "acs" -> x.hasAcs = on;
        case "stroke" -> x.hasStroke = on;
        case "hf" -> x.hasHf = on;
        case "bleeding" -> x.hasBleeding = on;
        case "revasc" -> x.hasRevasc = on;
        default -> x.hasOther = on;
      }
      LocalDate dt = on ? dateLenient(o.get("date")) : null;
      if (dt != null && (first == null || dt.isBefore(first))) first = dt;
    }
    x.firstEventDate = first;
    return x;
  }

  /** @param imageData image_id → data URL。null なら画像本体を含めない（一覧用） */
  public static CathReport toDto(CathReportEntity e, Map<String, String> imageData) {
    CathReport d = new CathReport();
    d.id = e.id;
    d.patientRef = e.patientRef;
    d.status = e.status;
    d.verified = e.verified;
    ReportHeader h = new ReportHeader();
    HeaderEmb x = e.header == null ? new HeaderEmb() : e.header;
    h.studyDate = date(x.studyDate);
    h.cineNo = x.cineNo;
    h.pciNo = x.pciNo;
    h.accessionNo = x.accessionNo;
    h.secretaryChecked = x.secretaryChecked;
    h.summary = x.summary;
    h.submitted = x.submitted;
    h.qca = x.qca;
    h.registrant = x.registrant;
    d.header = h;
    d.cathRecord = e.cathRecord;
    d.cagLvg = e.cagLvg;
    d.pci = e.pci;
    d.pressureIvus = e.pressureIvus;
    d.pcps = e.pcps;
    d.conference = e.conference;
    d.restudy = e.restudy;

    d.history = new ArrayList<>();
    for (HistoryEmb y : e.history) {
      CathReport.History z = new CathReport.History();
      z.at = instant(y.at);
      z.by = y.by;
      z.action = y.action;
      d.history.add(z);
    }
    d.mace = new ArrayList<>();
    for (MaceEmb m : e.mace) d.mace.add(m.data);
    d.images = new ArrayList<>();
    for (ImageEmb y : e.images) {
      CathReport.Image z = new CathReport.Image();
      z.id = y.imageId;
      z.category = y.category;
      z.takenAt = date(y.takenAt);
      z.view = y.view;
      z.lesion = y.lesion;
      z.title = y.title;
      z.description = y.description;
      z.fileName = y.fileName;
      z.mimeType = y.mimeType;
      z.keyImage = y.keyImage;
      if (imageData != null) z.dataUrl = imageData.get(y.imageId);
      d.images.add(z);
    }
    d.createdAt = instant(e.createdAt);
    d.updatedAt = instant(e.updatedAt);
    d.version = e.version;
    return d;
  }
}
