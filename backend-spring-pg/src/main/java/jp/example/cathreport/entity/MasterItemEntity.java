package jp.example.cathreport.entity;

import jakarta.persistence.*;

/** マスタ項目（table: master_items）。kind = doctor / hospital / device */
@Entity
@Table(name = "master_items")
public class MasterItemEntity {
  public static final String DOCTOR = "doctor";
  public static final String HOSPITAL = "hospital";
  public static final String DEVICE = "device";

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  public Long id;
  public String kind;
  public String category;
  public String name;
  public int sortOrder;

  public MasterItemEntity() {}

  public MasterItemEntity(String kind, String category, String name, int sortOrder) {
    this.kind = kind;
    this.category = category;
    this.name = name;
    this.sortOrder = sortOrder;
  }
}
