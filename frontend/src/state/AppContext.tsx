import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { CathReport, Draft, Masters, Patient, SectionKey } from '../types/model';
import { AuthError, createAdapter, loadSettings, LocalStorageAdapter, RemoteStorageAdapter, saveSettings, type StorageAdapter, type StorageSettings } from '../storage';
import { hasPermission, type AuthUser, type Permission } from '../auth/permissions';
import { clearSession, loadSession, saveSession } from '../auth/session';
import { localLogin } from '../auth/localAuth';

/** Local Storage 用ログインの保存キー */
const LOCAL_AUTH = 'local';
import { createEmptyPatient, createEmptyReport, DEFAULT_MASTERS, SECTION_FACTORIES } from '../model/defaults';
import { deepEqual, getAt, setAt } from '../utils/path';
import { nowIso } from '../utils/date';
import { screenLabel, type ScreenKey } from './screens';
import type { FormApi } from '../form/FormContext';
import { OptionsProvider } from '../form/OptionsContext';
import { defaultOptionCategories, mergeWithDefaults, normalizeCategory, validateCategory, type OptionCategory } from '../model/optionMaster';

export interface ListFilter { from: string; to: string; q: string; status: string }

interface Confirm { title: string; message: ReactNode; okLabel?: string; danger?: boolean; onOk: () => void }

interface AppApi {
  settings: StorageSettings;
  adapter: StorageAdapter;
  changeSettings: (s: StorageSettings) => void;
  patients: Patient[];
  reports: CathReport[];
  masters: Masters;
  saveMasters: (m: Masters) => Promise<void>;
  /** 選択値マスタ（プログラムの定義と保存済みの内容を合わせたもの） */
  optionCategories: OptionCategory[];
  /** 選択値マスタを保存できるか（false = バックエンドが未対応。初期値で表示中） */
  optionMastersSupported: boolean;
  /** 1 カテゴリを保存。成功なら true */
  saveOptionCategory: (c: OptionCategory) => Promise<boolean>;
  loading: boolean;
  screen: ScreenKey;
  draft: Draft | null;
  original: Draft | null;
  isNew: boolean;
  isDirty: boolean;
  form: FormApi | null;
  filter: ListFilter;
  setFilter: (f: ListFilter) => void;
  filteredReports: CathReport[];
  patientOf: (r: CathReport) => Patient | undefined;
  /** 画面遷移（未保存の変更があれば確認ダイアログ） */
  guard: (fn: () => void) => void;
  goto: (s: ScreenKey) => void;
  openReport: (id: string, s?: ScreenKey) => void;
  newReport: (patient: Patient | null) => void;
  save: () => Promise<void>;
  deleteReport: (id: string) => void;
  clearSection: (section: SectionKey) => void;
  refresh: () => Promise<void>;
  resetSample: () => void;
  toast: (msg: string, kind?: 'ok' | 'err') => void;
  confirm: (c: Confirm) => void;
  /** 帳票（レポート印刷）の表示 */
  printing: boolean;
  setPrinting: (v: boolean) => void;
  // ダイアログ状態（App.tsx が描画）
  pendingNav: boolean;
  resolvePending: (discard: boolean) => void;
  confirmState: Confirm | null;
  closeConfirm: () => void;
  toastState: { msg: string; kind: 'ok' | 'err'; id: number } | null;
  // ---- 認証（Remote DB のみ。Local Storage では認証なし）
  /** ログイン中の利用者（Local では null） */
  user: AuthUser | null;
  /** ログインが必要（未ログイン・期限切れ。保存先にかかわらず） */
  authRequired: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  /** 操作の権限（Local では常に true。最終的な判断はサーバー） */
  can: (p: Permission) => boolean;
}

const Ctx = createContext<AppApi | null>(null);
export const useApp = () => {
  const c = useContext(Ctx);
  if (!c) throw new Error('AppProvider がありません');
  return c;
};

/** 確定済みでも変更できる項目 */
const UNLOCKED = new Set(['report.status', 'report.verified', 'report.header.registrant']);

const byDateDesc = (a: CathReport, b: CathReport) =>
  (b.header.studyDate || '').localeCompare(a.header.studyDate || '') || (b.header.cineNo || '').localeCompare(a.header.cineNo || '');

export function AppProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<StorageSettings>(loadSettings);
  // ---- 認証：トークンは ref（アダプターが毎回参照）と sessionStorage に保持
  const tokenRef = useRef<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const userRef = useRef<AuthUser | null>(null);
  userRef.current = user;
  const [authChecked, setAuthChecked] = useState(false);
  const onUnauthorized = useRef<() => void>(() => undefined);
  const adapter = useMemo(
    () => createAdapter(settings, { token: () => tokenRef.current, onUnauthorized: () => onUnauthorized.current?.(), user: () => userRef.current }),
    [settings],
  );
  const [patients, setPatients] = useState<Patient[]>([]);
  const [reports, setReports] = useState<CathReport[]>([]);
  const [masters, setMasters] = useState<Masters>(DEFAULT_MASTERS);
  const [optionCategories, setOptionCategories] = useState<OptionCategory[]>(defaultOptionCategories);
  const [optionMastersSupported, setOptionMastersSupported] = useState(true);
  const [loading, setLoading] = useState(false);
  const [screen, setScreen] = useState<ScreenKey>('list');
  const [original, setOriginal] = useState<Draft | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [highlight, setHighlight] = useState(false);
  const [pending, setPending] = useState<(() => void) | null>(null);
  const [confirmState, setConfirmState] = useState<Confirm | null>(null);
  const [printing, setPrinting] = useState(false);
  const [toastState, setToastState] = useState<AppApi['toastState']>(null);
  const [filter, setFilter] = useState<ListFilter>({ from: '', to: '', q: '', status: '' });

  const toast = useCallback((msg: string, kind: 'ok' | 'err' = 'ok') => setToastState({ msg, kind, id: Date.now() }), []);

  // 401 を受けたら：ログイン情報を消してログインダイアログを出す（編集中の内容はそのまま残す）
  onUnauthorized.current = () => {
    clearSession(settings.remoteUrl);
    tokenRef.current = null;
    setUser(null);
  };

  // 保存先が変わったら：Remote なら保存済みのログイン情報を確認する
  useEffect(() => {
    let alive = true;
    setAuthChecked(false);
    setUser(null);
    tokenRef.current = null;
    if (!(adapter instanceof RemoteStorageAdapter)) {
      // Local Storage もデモ用の利用者でログインする（タブを閉じるまで有効）
      const ls = loadSession(LOCAL_AUTH);
      if (ls) setUser(ls.user);
      setAuthChecked(true);
      return;
    }
    const s = loadSession(settings.remoteUrl);
    if (!s) {
      setAuthChecked(true);
      return;
    }
    tokenRef.current = s.token;
    adapter
      .me()
      .then((u) => alive && setUser(u))
      .catch(() => undefined)
      .finally(() => alive && setAuthChecked(true));
    return () => {
      alive = false;
    };
  }, [adapter, settings.remoteUrl]);

  // 保存先にかかわらずログインが必要（Local はデモ用の利用者・ブラウザ内で照合、Remote はサーバーで認証）
  const authRequired = authChecked && !user;
  const authorized = !!user;

  const can = useCallback((p: Permission) => hasPermission(user, p), [user]);

  const refresh = useCallback(async () => {
    if (!authorized) return;
    setLoading(true);
    try {
      const [p, r, m] = await Promise.all([adapter.listPatients(), adapter.listReports(), adapter.getMasters()]);
      setPatients(p);
      setReports(r);
      setMasters(m);
      // 選択値マスタ：取得できなくても入力は続けられる（プログラムの初期値で表示）
      try {
        const saved = await adapter.getOptionMasters();
        setOptionCategories(mergeWithDefaults(saved));
        setOptionMastersSupported(saved !== null || adapter.kind === 'local');
      } catch (e) {
        setOptionCategories(defaultOptionCategories());
        if (!(e instanceof AuthError)) toast(`選択値マスタの取得に失敗しました（初期値で表示します）: ${(e as Error).message}`, 'err');
      }
    } catch (e) {
      setPatients([]);
      setReports([]);
      if (!(e instanceof AuthError)) toast(`データ取得に失敗しました: ${(e as Error).message}`, 'err');
    } finally {
      setLoading(false);
    }
  }, [adapter, toast, authorized]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const isDirty = useMemo(() => !!draft && (isNew || !deepEqual(draft, original)), [draft, original, isNew]);

  useEffect(() => {
    const h = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', h);
    return () => window.removeEventListener('beforeunload', h);
  }, [isDirty]);

  const guard = useCallback(
    (fn: () => void) => {
      if (isDirty) setPending(() => fn);
      else fn();
    },
    [isDirty],
  );

  const resolvePending = (discard: boolean) => {
    const fn = pending;
    setPending(null);
    if (discard) {
      if (isNew) {
        setDraft(null);
        setOriginal(null);
        setIsNew(false);
      } else {
        setDraft(original);
      }
      setHighlight(false);
      fn?.();
    } else {
      // キャンセル：遷移せず、変更項目を黄色で表示
      setHighlight(true);
    }
  };

  const loadDraft = (d: Draft, newFlag: boolean) => {
    setOriginal(d);
    setDraft(d);
    setIsNew(newFlag);
    setHighlight(false);
  };

  const openReport = (id: string, s?: ScreenKey) =>
    guard(async () => {
      try {
        const r = await adapter.getReport(id);
        if (!r) return toast('レコードが見つかりません', 'err');
        const p = (await adapter.getPatient(r.patientRef)) ?? { ...createEmptyPatient(), id: r.patientRef || createEmptyPatient().id };
        loadDraft({ patient: p, report: r }, false);
        setScreen(s ?? (screen === 'list' || screen === 'stats' ? 'cathRecord' : screen));
      } catch (e) {
        toast(`読込に失敗しました: ${(e as Error).message}`, 'err');
      }
    });

  const newReport = (patient: Patient | null) =>
    guard(() => {
      const p = patient ?? createEmptyPatient();
      const r = createEmptyReport(p.id);
      r.cathRecord.doctors.attending = p.primaryDoctor;
      r.cathRecord.doctors.referralHospital = p.referral.hospital;
      r.cathRecord.doctors.referralDoctor = p.referral.doctor;
      r.history = [{ at: nowIso(), by: '', action: '新規作成' }];
      loadDraft({ patient: p, report: r }, true);
      setScreen(patient ? 'cathRecord' : 'patient');
    });

  const save = async () => {
    if (!draft || !original) return;
    if (!can('edit')) return toast('保存する権限がありません（閲覧のみ）', 'err');
    const miss: string[] = [];
    if (!draft.patient.patientId.trim()) miss.push('患者ID');
    if (!draft.patient.name.trim()) miss.push('氏名');
    if (!draft.report.header.studyDate) miss.push('施行日');
    if (miss.length) {
      toast(`必須項目が未入力です: ${miss.join('、')}`, 'err');
      return;
    }
    const t = nowIso();
    const patientChanged = isNew || !deepEqual(draft.patient, original.patient);
    const p: Patient = patientChanged ? { ...draft.patient, updatedAt: t } : draft.patient;
    const r: CathReport = {
      ...draft.report,
      patientRef: p.id,
      updatedAt: t,
      // 記録者はログイン中の利用者（Remote はサーバーでも上書き）
      history: [...draft.report.history, { at: t, by: user?.displayName || draft.report.header.registrant, action: `保存（${screenLabel(screen)}）` }],
    };
    try {
      // サーバーの返却値（version・更新日時）で状態を更新する（PostgreSQL 版の楽観ロックに必要）
      const savedPatient = patientChanged ? await adapter.savePatient(p) : p;
      const saved = await adapter.saveReport(r);
      loadDraft({ patient: savedPatient, report: saved }, false);
      await refresh();
      toast('保存しました');
    } catch (e) {
      toast(e instanceof AuthError ? 'ログインの有効期限が切れました。ログインしてから、もう一度保存してください（入力内容は残っています）' : `保存に失敗しました: ${(e as Error).message}`, 'err');
    }
  };

  const confirm = (c: Confirm) => setConfirmState(c);

  const deleteReport = (id: string) =>
    !can('deleteReport')
      ? toast('レコードを削除する権限がありません', 'err')
      : confirm({
      title: 'レコード削除',
      message: 'このカテレポートを削除します。元に戻せません。よろしいですか？',
      okLabel: '削除',
      danger: true,
      onOk: async () => {
        try {
          await adapter.deleteReport(id);
          if (draft?.report.id === id) {
            setDraft(null);
            setOriginal(null);
            setIsNew(false);
            setScreen('list');
          }
          await refresh();
          toast('削除しました');
        } catch (e) {
          toast(`削除に失敗しました: ${(e as Error).message}`, 'err');
        }
      },
    });

  const clearSection = (section: SectionKey) =>
    draft?.report.status === '確定'
      ? toast('確定済みのレポートはクリアできません（「確定」をクリックして入力中に戻してください）', 'err')
      : confirm({
      title: '入力内容のクリア',
      message: `「${screenLabel(section as ScreenKey)}」の入力内容をすべて消去します（保存するまで確定しません）。`,
      okLabel: 'クリア',
      danger: true,
      onOk: () => setDraft((d) => (d ? setAt(d, `report.${section}`, SECTION_FACTORIES[section]()) : d)),
    });

  const changeSettings = (s: StorageSettings) =>
    guard(() => {
      saveSettings(s);
      setSettings(s);
      setDraft(null);
      setOriginal(null);
      setIsNew(false);
      setScreen('list');
    });

  const resetSample = () =>
    !can('seed')
      ? toast('サンプルデータを投入する権限がありません（管理者のみ）', 'err')
      : confirm({
      title: 'サンプルデータ投入',
      message: `現在の保存先（${settings.kind === 'local' ? 'Local Storage' : 'Remote DB'}）のデータをサンプルデータで置き換えます。`,
      okLabel: '投入',
      danger: true,
      onOk: async () => {
        try {
          await adapter.resetWithSample();
          setDraft(null);
          setOriginal(null);
          setIsNew(false);
          setScreen('list');
          await refresh();
          toast('サンプルデータを投入しました');
        } catch (e) {
          toast(`失敗しました: ${(e as Error).message}`, 'err');
        }
      },
    });

  const saveMasters = async (m: Masters) => {
    if (!can('masters')) return toast('マスタを編集する権限がありません（管理者のみ）', 'err');
    try {
      setMasters(await adapter.saveMasters(m));
      toast('マスタを保存しました');
    } catch (e) {
      toast(`マスタ保存に失敗しました: ${(e as Error).message}`, 'err');
    }
  };

  const saveOptionCategory = async (c: OptionCategory): Promise<boolean> => {
    if (!can('masters')) {
      toast('選択値マスタを編集する権限がありません（管理者のみ）', 'err');
      return false;
    }
    const n = normalizeCategory({ ...c, updatedBy: user?.displayName ?? user?.username });
    const errors = validateCategory(n);
    if (errors.length) {
      toast(errors.join(' / '), 'err');
      return false;
    }
    try {
      const saved = await adapter.saveOptionCategory(n);
      setOptionCategories((list) => mergeWithDefaults(list.map((x) => (x.code === saved.code ? saved : x))));
      toast(`選択値「${c.name}」を保存しました`);
      return true;
    } catch (e) {
      toast(`選択値の保存に失敗しました: ${(e as Error).message}`, 'err');
      return false;
    }
  };

  const optionMap = useMemo(() => new Map(optionCategories.map((c) => [c.code, c])), [optionCategories]);

  const patientMap = useMemo(() => new Map(patients.map((p) => [p.id, p])), [patients]);
  const patientOf = useCallback((r: CathReport) => patientMap.get(r.patientRef), [patientMap]);

  const filteredReports = useMemo(() => {
    const q = filter.q.trim().toLowerCase();
    return reports
      .filter((r) => {
        if (filter.from && r.header.studyDate < filter.from) return false;
        if (filter.to && r.header.studyDate > filter.to) return false;
        if (filter.status === 'unverified' && r.verified) return false;
        if (filter.status && filter.status !== 'unverified' && r.status !== filter.status) return false;
        if (!q) return true;
        const p = patientMap.get(r.patientRef);
        const hay = [p?.patientId, p?.name, p?.kana, r.header.cineNo, r.header.pciNo, r.cathRecord.exam.disease, r.cathRecord.exam.examItems, ...r.cathRecord.doctors.operators, r.cathRecord.doctors.attending]
          .join(' ')
          .toLowerCase();
        return hay.includes(q);
      })
      .sort(byDateDesc);
  }, [reports, filter, patientMap]);

  const form: FormApi | null = useMemo(
    () =>
      draft && original
        ? {
            value: draft,
            original,
            highlight,
            // 確定済みレポートは全項目ロック（ステータス・照合・登録者のみ変更可）。閲覧のみの利用者は全項目ロック
            readOnly: draft.report.status === '確定' || !can('edit'),
            screen,
            goto: (s) => goto(s),
            set: (path, v) => {
              if (!can('edit')) return;
              if (path === 'report.status' && !can('confirm')) return toast('確定・確定解除の権限がありません（医師・管理者）', 'err');
              if (path === 'report.verified' && !can('verify')) return toast('照合の権限がありません（医師・管理者）', 'err');
              setDraft((d) => (d && (d.report.status !== '確定' || UNLOCKED.has(path)) ? setAt(d, path, v) : d));
            },
            setMany: (entries) =>
              setDraft((d) => {
                if (!d || d.report.status === '確定' || !can('edit')) return d;
                let x = d;
                for (const [p, v] of entries) if (getAt(x, p) !== v) x = setAt(x, p, v);
                return x;
              }),
          }
        : null,
    [draft, original, highlight, screen, isNew, can],
  );

  const login = async (username: string, password: string) => {
    if (!(adapter instanceof RemoteStorageAdapter)) {
      const u = await localLogin(username, password); // 失敗はログイン画面に表示（例外のまま返す）
      saveSession(LOCAL_AUTH, { token: 'local', expiresAt: new Date(Date.now() + 8 * 3600_000).toISOString(), user: u });
      userRef.current = u;
      setUser(u);
      if (adapter instanceof LocalStorageAdapter) adapter.record('LOGIN', 'user', u.username);
      toast(`${u.displayName} さんでログインしました`);
      return;
    }
    const r = await adapter.login(username, password); // 失敗はログイン画面に表示（例外のまま返す）
    tokenRef.current = r.token;
    saveSession(settings.remoteUrl, r);
    setUser(r.user);
    toast(`${r.user.displayName} さんでログインしました`);
  };

  const logout = () =>
    guard(async () => {
      if (adapter instanceof RemoteStorageAdapter) await adapter.logout().catch(() => undefined);
      else if (adapter instanceof LocalStorageAdapter && user) adapter.record('LOGOUT', 'user', user.username);
      clearSession(settings.remoteUrl);
      clearSession(LOCAL_AUTH);
      tokenRef.current = null;
      setUser(null);
      setDraft(null);
      setOriginal(null);
      setIsNew(false);
      setPatients([]);
      setReports([]);
      setScreen('list');
    });

  const goto = (s: ScreenKey) => {
    if (s === screen) return;
    guard(() => setScreen(s));
  };

  const api: AppApi = {
    settings, adapter, changeSettings, patients, reports, masters, saveMasters, optionCategories, optionMastersSupported, saveOptionCategory, loading, screen, draft, original, isNew, isDirty, form,
    filter, setFilter, filteredReports, patientOf, guard, goto, openReport, newReport, save, deleteReport, clearSection, refresh,
    resetSample, toast, confirm, printing, setPrinting,
    pendingNav: pending !== null,
    resolvePending,
    confirmState,
    closeConfirm: () => setConfirmState(null),
    toastState,
    user,
    authRequired,
    login,
    logout,
    can,
  };
  return (
    <Ctx.Provider value={api}>
      <OptionsProvider value={optionMap}>{children}</OptionsProvider>
    </Ctx.Provider>
  );
}
