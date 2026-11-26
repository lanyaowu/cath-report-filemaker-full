package jp.example.cathreport.service;

import java.util.ArrayList;
import java.util.List;
import jp.example.cathreport.api.Masters;
import jp.example.cathreport.entity.MasterItemEntity;
import jp.example.cathreport.repository.MasterItemRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class MastersService {
  private final MasterItemRepository items;

  public MastersService(MasterItemRepository items) {
    this.items = items;
  }

  @Transactional(readOnly = true)
  public Masters get() {
    Masters m = new Masters();
    for (MasterItemEntity i : items.findAllByOrderByKindAscSortOrderAscIdAsc()) {
      switch (i.kind) {
        case MasterItemEntity.DOCTOR -> m.doctors.add(i.name);
        case MasterItemEntity.HOSPITAL -> m.hospitals.add(i.name);
        case MasterItemEntity.DEVICE -> m.devices.add(new Masters.DeviceMaster(i.category, i.name));
        default -> {}
      }
    }
    return m;
  }

  /** マスタ全体を置き換える（画面のマスタ編集は全件保存） */
  @Transactional
  public Masters save(Masters m) {
    items.deleteAllInBatch();
    List<MasterItemEntity> rows = new ArrayList<>();
    int i = 0;
    for (String s : nn(m.doctors)) if (notBlank(s)) rows.add(new MasterItemEntity(MasterItemEntity.DOCTOR, null, s.trim(), i++));
    i = 0;
    for (String s : nn(m.hospitals)) if (notBlank(s)) rows.add(new MasterItemEntity(MasterItemEntity.HOSPITAL, null, s.trim(), i++));
    i = 0;
    for (Masters.DeviceMaster d : nn(m.devices)) {
      if (d != null && notBlank(d.name)) rows.add(new MasterItemEntity(MasterItemEntity.DEVICE, d.category, d.name.trim(), i++));
    }
    items.saveAll(rows);
    return get();
  }

  private static <T> List<T> nn(List<T> l) {
    return l == null ? List.of() : l;
  }

  private static boolean notBlank(String s) {
    return s != null && !s.isBlank();
  }
}
