package jp.example.cathreport.repository;

import java.util.List;
import jp.example.cathreport.entity.MasterItemEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MasterItemRepository extends JpaRepository<MasterItemEntity, Long> {
  List<MasterItemEntity> findAllByOrderByKindAscSortOrderAscIdAsc();
}
