// MongoDB 版（Node.js・Spring Boot + MongoDB）のデータ移行：既往歴・併存症を J-PCI からカテ記録へ移す（不足項目 G-01）
//   実行：mongosh "mongodb://localhost:27017/cathreport" tools/migrate/mongo_v4_history.js
//   PostgreSQL 版の V4__history_to_cath_record.sql と同じ内容。何度実行しても結果は同じ。
//   画面も読込時に同じ移行を行うため、実行しなくても表示・保存は正しく動く（DB 上のデータを揃えるための任意の作業）。
const KEYS = ['priorMI', 'priorHF', 'pciHx', 'cabgHx', 'renal', 'copd', 'pad'];
let n = 0;
db.cath_reports.find({ $or: KEYS.map((k) => ({ [`pci.jpci.bg.${k}`]: { $exists: true } })) }).forEach((r) => {
  const bg = (r.pci && r.pci.jpci && r.pci.jpci.bg) || {};
  const risk = (r.cathRecord && r.cathRecord.risk) || {};
  const set = {};
  const unset = {};
  for (const k of KEYS) {
    if (!(k in bg)) continue;
    if (bg[k] && !risk[k]) set[`cathRecord.risk.${k}`] = bg[k];
    unset[`pci.jpci.bg.${k}`] = '';
  }
  const u = { $unset: unset };
  if (Object.keys(set).length) u.$set = set;
  db.cath_reports.updateOne({ _id: r._id }, u);
  n++;
});
print(`移行したレポート: ${n} 件`);
