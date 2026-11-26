import { Router, type NextFunction, type Request, type Response } from 'express';
import type { Document, Filter } from 'mongodb';
import { allow, audit, AUDIT, auditOut } from '../auth.js';
import { auditDiff } from '../auditDiff.js';
import { config } from '../config.js';
import { coll, COLL, fromDoc, seed, toDoc } from '../db.js';
import { checkReportSave, checkVersion, requirePermission, RuleError, stampHistory } from '../rules.js';
import { checkOptionItems, optionChanges, summarizeOptionChange, type OptionCategory } from '../options.js';

type Handler = (req: Request, res: Response) => Promise<unknown>;
/** 業務ルール違反（RuleError）は {"error"} で返し、それ以外は共通のエラー処理へ */
const wrap = (h: Handler) => (req: Request, res: Response, next: NextFunction) =>
  h(req, res).catch((e) => (e instanceof RuleError ? res.status(e.status).json({ error: e.message }) : next(e)));

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** 本文の id（PUT はパスの id）がなければ 400（Spring 版と同じメッセージ） */
function requireId(id: unknown, res: Response): id is string {
  if (typeof id === 'string' && id.trim() !== '') return true;
  res.status(400).json({ error: 'id が必要です' });
  return false;
}

function requireBody(req: Request, res: Response, fields: string[]) {
  const missing = fields.filter((f) => req.body?.[f] === undefined || req.body?.[f] === null);
  if (missing.length) {
    res.status(400).json({ error: `必須項目がありません: ${missing.join(', ')}` });
    return false;
  }
  return true;
}

/** 楽観ロック用の version（保存前のデータには無いので 0 とみなす） */
const withVersion = (d: Document | null) => (d ? { ...fromDoc(d), version: Number(d.version ?? 0) } : null);
/** version が保存時と同じ場合だけ置き換える（同時保存の競合を防ぐ） */
const versionFilter = (id: string, v: number) =>
  (v === 0 ? { _id: id, $or: [{ version: 0 }, { version: { $exists: false } }] } : { _id: id, version: v }) as Filter<Document>;

export const api = Router();

api.get('/health', (_req, res) => res.json({ status: 'ok', backend: 'node', time: new Date().toISOString() }));

// ---------------- 患者 ----------------
api.get(
  '/patients',
  wrap(async (req, res) => {
    const q = String(req.query.q ?? '').trim();
    const filter: Filter<Document> = q
      ? { $or: ['patientId', 'name', 'kana'].map((f) => ({ [f]: { $regex: escapeRe(q), $options: 'i' } })) }
      : {};
    const list = await coll(COLL.patients).find(filter).sort({ kana: 1 }).toArray();
    res.json(list.map(withVersion));
  }),
);

api.get(
  '/patients/:id',
  wrap(async (req, res) => {
    const p = await coll(COLL.patients).findOne({ _id: req.params.id } as Filter<Document>);
    if (!p) return res.status(404).json({ error: 'not found' });
    await audit(req, 'VIEW_PATIENT', 'patient', req.params.id);
    res.json(withVersion(p));
  }),
);

const upsertPatient: Handler = async (req, res) => {
  requirePermission(req.user, 'edit');
  const id = req.params.id ?? req.body?.id;
  if (!requireBody(req, res, ['patientId', 'name']) || !requireId(id, res)) return;
  const dup = await coll(COLL.patients).findOne({ patientId: req.body.patientId, _id: { $ne: id } } as Filter<Document>);
  if (dup) return res.status(409).json({ error: `患者ID ${req.body.patientId} は既に登録されています` });
  const old = await coll(COLL.patients).findOne({ _id: id } as Filter<Document>);
  const version = checkVersion('患者', old, req.body.version);
  const now = new Date().toISOString();
  const body = { ...req.body, id, version, updatedAt: now, createdAt: old?.createdAt ?? req.body.createdAt ?? now };
  if (old) {
    const r = await coll(COLL.patients).replaceOne(versionFilter(id, Number(old.version ?? 0)), toDoc(body));
    if (r.matchedCount === 0) throw new RuleError(409, 'この患者は他の端末で更新されています。再読み込みしてください');
  } else {
    await coll(COLL.patients).insertOne(toDoc(body));
  }
  await audit(req, old ? 'UPDATE_PATIENT' : 'CREATE_PATIENT', 'patient', id, '', auditDiff(old ? fromDoc(old) : null, body));
  res.json(body);
};
api.post('/patients', wrap(upsertPatient));
api.put('/patients/:id', wrap(upsertPatient));

api.delete(
  '/patients/:id',
  allow('deletePatient'),
  wrap(async (req, res) => {
    const used = await coll(COLL.reports).countDocuments({ patientRef: req.params.id });
    if (used) return res.status(409).json({ error: `この患者には ${used} 件のレポートがあるため削除できません` });
    const r = await coll(COLL.patients).deleteOne({ _id: req.params.id } as Filter<Document>);
    if (r.deletedCount) await audit(req, 'DELETE_PATIENT', 'patient', req.params.id);
    res.status(204).end();
  }),
);

// ---------------- カテレポート ----------------
api.get(
  '/reports',
  wrap(async (req, res) => {
    const filter: Filter<Document> = {};
    const { from, to, patientRef, status } = req.query as Record<string, string | undefined>;
    if (from || to) filter['header.studyDate'] = { ...(from ? { $gte: from } : {}), ...(to ? { $lte: to } : {}) };
    if (patientRef) filter.patientRef = patientRef;
    if (status) filter.status = status;
    // 一覧では画像本体を返さない（データ量削減）
    const list = await coll(COLL.reports)
      .find(filter, { projection: { 'images.dataUrl': 0 } })
      .sort({ 'header.studyDate': -1 })
      .limit(Number(req.query.limit ?? 5000))
      .toArray();
    res.json(list.map(withVersion));
  }),
);

api.get(
  '/reports/:id',
  wrap(async (req, res) => {
    const r = await coll(COLL.reports).findOne({ _id: req.params.id } as Filter<Document>);
    if (!r) return res.status(404).json({ error: 'not found' });
    await audit(req, 'VIEW_REPORT', 'report', req.params.id);
    res.json(withVersion(r));
  }),
);

const upsertReport: Handler = async (req, res) => {
  const id = req.params.id ?? req.body?.id;
  if (!requireBody(req, res, ['patientRef', 'header']) || !requireId(id, res)) return;
  const patient = await coll(COLL.patients).findOne({ _id: req.body.patientRef } as Filter<Document>);
  if (!patient) return res.status(400).json({ error: '患者が存在しません（patientRef）' });
  const oldDoc = await coll(COLL.reports).findOne({ _id: id } as Filter<Document>);
  const old = oldDoc ? (fromDoc(oldDoc) as Record<string, unknown>) : null;
  const body = { ...req.body, id } as Record<string, unknown>;
  // 権限 → 楽観ロック（他の端末の更新を先に知らせる）→ 業務ルール（確定ロック・履歴）
  requirePermission(req.user, 'edit');
  const version = checkVersion('レポート', oldDoc, req.body.version);
  checkReportSave(req.user, old, body);
  stampHistory(req.user!, Array.isArray(old?.history) ? (old!.history as unknown[]).length : 0, body);
  const now = new Date().toISOString();
  Object.assign(body, { version, updatedAt: now, createdAt: old?.createdAt ?? req.body.createdAt ?? now });
  if (oldDoc) {
    const r = await coll(COLL.reports).replaceOne(versionFilter(id, Number(oldDoc.version ?? 0)), toDoc(body as { id: string }));
    if (r.matchedCount === 0) throw new RuleError(409, 'このレポートは他の端末で更新されています。再読み込みしてください');
  } else {
    await coll(COLL.reports).insertOne(toDoc(body as { id: string }));
  }
  const detail = [old?.status !== body.status ? `status:${old?.status ?? '-'}→${body.status}` : '', !!old?.verified !== !!body.verified ? `verified:${!!body.verified}` : '']
    .filter(Boolean).join(' ');
  await audit(req, old ? 'UPDATE_REPORT' : 'CREATE_REPORT', 'report', id, detail, auditDiff(old, body));
  res.json(body);
};
/** レポートの変更履歴：そのレポートと患者の作成・削除と、項目が変わった更新（変わった項目つき。新しい順。閲覧の権限） */
api.get(
  '/reports/:id/history',
  wrap(async (req, res) => {
    requirePermission(req.user, 'read');
    const r = await coll(COLL.reports).findOne({ _id: req.params.id } as Filter<Document>, { projection: { patientRef: 1 } });
    const targets: Filter<Document>[] = [{ targetType: 'report', targetId: req.params.id }];
    if (r?.patientRef) targets.push({ targetType: 'patient', targetId: String(r.patientRef) });
    const list = await coll(AUDIT)
      .find({ $and: [{ $or: targets }, { $or: [{ action: { $regex: '^(CREATE|DELETE)_' } }, { changeCount: { $gt: 0 } }] }] } as Filter<Document>)
      .sort({ at: -1, _id: -1 })
      .limit(1000)
      .toArray();
    res.json(list.map(auditOut));
  }),
);
api.post('/reports', wrap(upsertReport));
api.put('/reports/:id', wrap(upsertReport));

api.delete(
  '/reports/:id',
  allow('deleteReport'),
  wrap(async (req, res) => {
    const r = await coll(COLL.reports).findOne({ _id: req.params.id } as Filter<Document>, { projection: { status: 1 } });
    if (r?.status === '確定') return res.status(409).json({ error: '確定済みのレポートは削除できません（ステータスを「入力中」に戻してください）' });
    const d = await coll(COLL.reports).deleteOne({ _id: req.params.id } as Filter<Document>);
    if (d.deletedCount) await audit(req, 'DELETE_REPORT', 'report', req.params.id);
    res.status(204).end();
  }),
);

// ---------------- マスタ ----------------
api.get(
  '/masters',
  wrap(async (_req, res) => {
    const m = await coll(COLL.masters).findOne({ _id: 'default' } as Filter<Document>);
    if (!m) return res.status(404).json({ error: 'not found' });
    const { _id, ...rest } = m;
    void _id;
    res.json(rest);
  }),
);

api.put(
  '/masters',
  allow('masters'),
  wrap(async (req, res) => {
    const { doctors = [], hospitals = [], devices = [] } = req.body ?? {};
    await coll(COLL.masters).replaceOne({ _id: 'default' } as Filter<Document>, { doctors, hospitals, devices }, { upsert: true });
    await audit(req, 'UPDATE_MASTERS', 'masters', 'default');
    res.json({ doctors, hospitals, devices });
  }),
);

// ---------------- 選択値マスタ（画面の選択肢） ----------------
const optionOut = (d: Document) => {
  const { _id, ...rest } = d;
  return { code: String(_id), ...rest, version: Number(d.version ?? 0) } as OptionCategory;
};

api.get(
  '/options',
  wrap(async (_req, res) => {
    const list = await coll(COLL.options).find({}).sort({ _id: 1 }).toArray();
    res.json(list.map(optionOut));
  }),
);

api.get(
  '/options/:code',
  wrap(async (req, res) => {
    const d = await coll(COLL.options).findOne({ _id: req.params.code } as Filter<Document>);
    if (!d) return res.status(404).json({ error: 'not found' });
    res.json(optionOut(d));
  }),
);

/** 1 カテゴリの選択値を保存（管理者のみ）。version で同時更新を検知し、変更前の内容を履歴に残す */
api.put(
  '/options/:code',
  allow('masters'),
  wrap(async (req, res) => {
    const doc = await coll(COLL.options).findOne({ _id: req.params.code } as Filter<Document>);
    if (!doc) return res.status(404).json({ error: `選択値マスタ ${req.params.code} がありません` });
    const old = optionOut(doc);
    const version = checkVersion('選択値マスタ', doc, req.body?.version);
    const items = checkOptionItems(old, req.body);
    const now = new Date().toISOString();
    const by = req.user?.displayName || req.user?.username || '';
    const r = await coll(COLL.options).updateOne(
      { _id: old.code, version: old.version === 0 ? { $in: [0, null] } : old.version } as Filter<Document>,
      { $set: { items, version, updatedAt: now, updatedBy: by } },
    );
    if (r.matchedCount === 0) throw new RuleError(409, 'この選択値は他の端末で更新されています。開き直してください');
    await coll(COLL.optionHistory).insertOne({ code: old.code, at: now, by, version: old.version, items: old.items } as Document);
    await audit(req, 'UPDATE_OPTIONS', 'option', old.code, summarizeOptionChange(old.items, items), optionChanges(old.items, items));
    res.json({ ...old, items, version, updatedAt: now, updatedBy: by });
  }),
);

// ---------------- 管理 ----------------
api.post(
  '/admin/seed',
  allow('seed'),
  wrap(async (req, res) => {
    if (!config.allowSeedApi) return res.status(403).json({ error: 'サンプルデータの投入は無効です（サーバーの ALLOW_SEED_API=true で有効）' });
    const r = await seed();
    await audit(req, 'SEED', 'all', '', JSON.stringify(r));
    res.json(r);
  }),
);
