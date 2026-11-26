import { MongoClient, type Collection, type Db, type Document, type Filter } from 'mongodb';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { config } from './config.js';

export const COLL = {
  patients: 'patients', reports: 'cath_reports', masters: 'masters',
  /** 選択値マスタ（_id = カテゴリコード、選択値は items に埋め込み） */
  options: 'option_categories',
  /** 選択値マスタの変更前の内容（保存のたびに 1 件） */
  optionHistory: 'option_category_history',
} as const;

let client: MongoClient | null = null;
let db: Db | null = null;

export async function connect(): Promise<Db> {
  if (db) return db;
  client = new MongoClient(config.mongoUri);
  await client.connect();
  db = client.db(config.dbName);
  await ensureIndexes(db);
  return db;
}

export async function close() {
  await client?.close();
  client = null;
  db = null;
}

export function coll<T extends Document = Document>(name: string): Collection<T> {
  if (!db) throw new Error('DB 未接続');
  return db.collection<T>(name);
}

async function ensureIndexes(d: Db) {
  await d.collection(COLL.patients).createIndex({ patientId: 1 }, { unique: true, sparse: true });
  await d.collection(COLL.patients).createIndex({ kana: 1 });
  await d.collection(COLL.reports).createIndex({ patientRef: 1 });
  await d.collection(COLL.reports).createIndex({ 'header.studyDate': -1 });
  await d.collection(COLL.reports).createIndex({ 'header.cineNo': 1 });
  await d.collection(COLL.reports).createIndex({ status: 1, verified: 1 });
  await d.collection('audit_log').createIndex({ at: -1 });
  await d.collection('audit_log').createIndex({ username: 1, at: -1 });
  await d.collection('audit_log').createIndex({ targetType: 1, targetId: 1, at: -1 });
  await d.collection(COLL.optionHistory).createIndex({ code: 1, at: -1 });
}

/** API の id ⇔ MongoDB の _id 変換 */
export const toDoc = <T extends { id: string }>(o: T) => {
  const { id, ...rest } = o as T & { _id?: unknown };
  delete (rest as { _id?: unknown })._id;
  return { _id: id, ...rest } as unknown as Document;
};
export const fromDoc = (d: Document | null) => {
  if (!d) return null;
  const { _id, ...rest } = d;
  return { id: String(_id), ...rest };
};

async function readJson(file: string) {
  return JSON.parse(await readFile(path.resolve(config.sampleDir, file), 'utf-8'));
}

/** サンプルデータ投入（既存データは削除） */
export async function seed() {
  const [patients, reports, masters] = await Promise.all([readJson('patients.json'), readJson('reports.json'), readJson('masters.json')]);
  await coll(COLL.patients).deleteMany({});
  await coll(COLL.reports).deleteMany({});
  await coll(COLL.masters).deleteMany({});
  if (patients.length) await coll(COLL.patients).insertMany(patients.map(toDoc));
  if (reports.length) await coll(COLL.reports).insertMany(reports.map(toDoc));
  await coll(COLL.masters).insertOne({ _id: 'default', ...masters } as unknown as Document);
  return { patients: patients.length, reports: reports.length };
}

/**
 * 選択値マスタの初期データ（sample-data/option-masters.json。tools/gen_option_masters.ts で作成）を入れる。
 * - 無いカテゴリだけ追加する（施設で編集した内容は上書きしない）。起動のたびに実行。
 * - 標準の分類（editable=false）は、名称・選択値をプログラムの定義に合わせる。
 */
export async function seedOptionMasters() {
  const defs = (await readJson('option-masters.json')) as { code: string; editable: boolean; name: string; screen: string; items: unknown[] }[];
  let added = 0;
  for (const d of defs) {
    const r = await coll(COLL.options).updateOne(
      { _id: d.code } as Filter<Document>,
      d.editable
        ? { $setOnInsert: { editable: true, items: d.items, version: 0 }, $set: { name: d.name, screen: d.screen } }
        : { $setOnInsert: { version: 0 }, $set: { name: d.name, screen: d.screen, editable: false, items: d.items } },
      { upsert: true },
    );
    if (r.upsertedCount) added++;
  }
  if (added) console.log(`[seed] 選択値マスタの初期データを追加しました: ${added} カテゴリ`);
}

export async function seedIfEmpty() {
  const n = await coll(COLL.patients).estimatedDocumentCount();
  if (n === 0) {
    const r = await seed();
    console.log(`[seed] サンプルデータを投入しました: 患者 ${r.patients} 件 / レポート ${r.reports} 件`);
  }
}
