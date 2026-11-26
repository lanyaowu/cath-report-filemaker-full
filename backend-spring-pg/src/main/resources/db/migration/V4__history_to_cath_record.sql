-- =====================================================================
-- V4: 既往歴・併存症を J-PCI（pci.jpci.bg）からカテ記録（cath_record.risk）へ移す（不足項目 G-01）
--   対象：priorMI・priorHF・pciHx・cabgHx・renal・copd・pad
--   ・カテ記録側が空のときだけ J-PCI の値を移す（カテ記録に値があればそちらを残す）
--   ・移した後、J-PCI 側のキーは削除する（画面は J-PCI タブからカテ記録の値を参照する）
--   ・CTO の閉塞期間（lesions[].cto.duration）は画面が読込時に旧「Age of Occlusion」から補完するため、ここでは移さない
-- 画面（React・Thymeleaf）も読込時に同じ移行を行うため、この移行の前に保存されたデータも正しく表示される。
-- =====================================================================
UPDATE cath_reports r
SET cath_record = jsonb_set(
      COALESCE(r.cath_record, '{}'::jsonb),
      '{risk}',
      COALESCE(r.cath_record -> 'risk', '{}'::jsonb) || COALESCE((
        SELECT jsonb_object_agg(k, r.pci -> 'jpci' -> 'bg' -> k)
        FROM unnest(ARRAY['priorMI', 'priorHF', 'pciHx', 'cabgHx', 'renal', 'copd', 'pad']) AS k
        WHERE COALESCE(r.pci -> 'jpci' -> 'bg' ->> k, '') <> ''
          AND COALESCE(r.cath_record -> 'risk' ->> k, '') = ''
      ), '{}'::jsonb),
      true),
    pci = r.pci #- '{jpci,bg,priorMI}' #- '{jpci,bg,priorHF}' #- '{jpci,bg,pciHx}' #- '{jpci,bg,cabgHx}'
                #- '{jpci,bg,renal}' #- '{jpci,bg,copd}' #- '{jpci,bg,pad}'
WHERE r.pci -> 'jpci' -> 'bg' ?| ARRAY['priorMI', 'priorHF', 'pciHx', 'cabgHx', 'renal', 'copd', 'pad'];
