import { useEffect, useMemo, useState } from 'react';
import { useApp } from '../../state/AppContext';
import { Btn, Modal, Note } from '../common/ui';
import { deepEqual } from '../../utils/path';
import { fmtDateTime } from '../../utils/date';
import { tIn } from '../../i18n';
import { MAX_CODE_LENGTH, MAX_LABEL_LENGTH, validateCategory, type OptionCategory, type OptionItem } from '../../model/optionMaster';

/** 言語の表示名を 1 つ変える（空にしたら消す。全部消えたら undefined。未変更の比較を正しくするため） */
const withLabel = (l: Record<string, string> | undefined, lang: string, v: string): Record<string, string> | undefined => {
  const next = { ...(l ?? {}) };
  if (v) next[lang] = v;
  else delete next[lang];
  return Object.keys(next).length ? next : undefined;
};

/** 編集中の行（isNew = この画面で追加した行。コードの入力・行の削除ができる） */
type Row = OptionItem & { isNew?: boolean };
type EditCat = Omit<OptionCategory, 'items'> & { items: Row[] };

/** 保存する形にする：追加行でコードが空なら表示名をコードにする（既存の選択肢と同じ「値＝表示名」の形） */
const prepare = (c: EditCat): OptionCategory => ({
  ...c,
  items: c.items.map(({ isNew, ...it }) => (isNew && !it.code.trim() ? { ...it, code: it.label.trim() } : it)),
});

/**
 * 選択値マスタの編集（管理者のみ）。
 * - 左でカテゴリ（選択肢の種類）を選び、右で選択値を編集する。保存はカテゴリ単位。
 * - 保存済みの選択値は削除せず「使用」を外して使用停止にする（過去のレポートの値を残すため）。コードも変更できない。
 * - 標準の分類（🔒）は自動判定・レジストリで値を使うため、表示のみ。
 */
export function OptionMasterDialog({ onClose }: { onClose: () => void }) {
  const app = useApp();
  const cats = app.optionCategories;
  const [code, setCode] = useState(cats.find((c) => c.editable)?.code ?? cats[0]?.code ?? '');
  const saved = cats.find((c) => c.code === code);
  const [edit, setEdit] = useState<EditCat | undefined>(saved);
  const [q, setQ] = useState('');
  // 保存後（edit を空にした時）・カテゴリ切替後は、最新の保存内容を編集の起点にする
  useEffect(() => {
    if (!edit) setEdit(saved);
  }, [edit, saved]);
  const dirty = !!edit && !!saved && !deepEqual(edit, saved);
  const errors = edit && dirty ? validateCategory(prepare(edit)) : [];
  const readOnly = !edit?.editable || !app.optionMastersSupported;

  const groups = useMemo(() => {
    const m = new Map<string, OptionCategory[]>();
    for (const c of cats) {
      if (q && !`${c.name}${c.code}${c.items.map((i) => `${i.label} ${Object.values(i.labels ?? {}).join(' ')}`).join(' ')}`.toLowerCase().includes(q.toLowerCase())) continue;
      m.set(c.screen, [...(m.get(c.screen) ?? []), c]);
    }
    return [...m.entries()];
  }, [cats, q]);

  const select = (next: string) => {
    const go = () => {
      setCode(next);
      setEdit(cats.find((c) => c.code === next));
    };
    if (!dirty) return go();
    app.confirm({ title: '変更の破棄', message: `「${saved?.name}」の変更を保存していません。破棄して移動しますか？`, okLabel: '破棄して移動', danger: true, onOk: go });
  };
  const close = () => {
    if (!dirty) return onClose();
    app.confirm({ title: '変更の破棄', message: '保存していない変更があります。破棄して閉じますか？', okLabel: '破棄して閉じる', danger: true, onOk: onClose });
  };

  const setItems = (items: Row[]) => edit && setEdit({ ...edit, items });
  const patch = (i: number, p: Partial<Row>) => edit && setItems(edit.items.map((x, j) => (j === i ? { ...x, ...p } : x)));
  const move = (i: number, d: -1 | 1) => {
    if (!edit) return;
    const j = i + d;
    if (j < 0 || j >= edit.items.length) return;
    const items = [...edit.items];
    [items[i], items[j]] = [items[j], items[i]];
    setItems(items);
  };
  const add = () => edit && setItems([...edit.items, { code: '', label: '', active: true, sortOrder: (edit.items.length + 1) * 10, isNew: true }]);
  const remove = (i: number) => edit && setItems(edit.items.filter((_, j) => j !== i));

  const save = async () => {
    if (!edit) return;
    const ok = await app.saveOptionCategory(prepare(edit));
    if (ok) setEdit(undefined); // 保存後は最新（app.optionCategories）を編集の起点にする
  };
  const shown: EditCat | undefined = edit ?? saved;

  return (
    <Modal
      title="選択値マスタ"
      onClose={close}
      width={1240}
      footer={
        <>
          {!readOnly && (
            <Btn kind="primary" disabled={!dirty || errors.length > 0} onClick={() => void save()}>
              保存
            </Btn>
          )}
          {!readOnly && dirty && <Btn onClick={() => setEdit(saved)}>変更を戻す</Btn>}
          <Btn onClick={close}>閉じる</Btn>
        </>
      }
    >
      {!app.optionMastersSupported && (
        <Note style={{ marginBottom: 6 }}>
          接続中のバックエンドは選択値マスタに未対応のため、プログラムの初期値を表示しています（編集できません）。Node.js＋MongoDB 版、または Local Storage で編集できます。
        </Note>
      )}
      <div className="optm">
        <div className="optm-cats">
          <input className="inp" style={{ width: '100%', marginBottom: 4 }} placeholder="検索（名称・選択値）" value={q} onChange={(e) => setQ(e.target.value)} />
          <div className="scroll" style={{ maxHeight: 440 }}>
            {groups.map(([screen, list]) => (
              <div key={screen}>
                <div className="optm-group">{screen}</div>
                {list.map((c) => (
                  <button
                    type="button"
                    key={c.code}
                    className={`optm-cat${c.code === code ? ' active' : ''}`}
                    onClick={() => c.code !== code && select(c.code)}
                    title={c.editable ? c.code : `${c.code}（標準の分類・編集不可）`}
                  >
                    {!c.editable && <span className="optm-lock">🔒</span>}
                    {c.name}
                    <span className="optm-count">{c.items.filter((i) => i.active).length}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>
        <div className="optm-items">
          {shown && (
            <>
              <div className="optm-head">
                <b>{shown.name}</b>
                <span className="small">（{shown.code}・{shown.screen}）</span>
                <span className="small optm-meta">
                  {shown.version > 0 ? `版 ${shown.version}${shown.updatedAt ? `・${fmtDateTime(shown.updatedAt)}` : ''}${shown.updatedBy ? `・${shown.updatedBy}` : ''}` : '初期値（未変更）'}
                </span>
              </div>
              {!shown.editable && <Note color="#555">標準の分類で、自動判定・J-PCI などで値を使うため編集できません。</Note>}
              <div className="scroll" style={{ maxHeight: 400 }}>
                <table className="tbl optm-tbl">
                  <thead>
                    <tr>
                      <th style={{ width: 54 }}>順序</th>
                      <th style={{ width: 190 }}>コード（保存される値）</th>
                      <th>表示名</th>
                      <th title="空なら日本語の表示名を辞書で訳して表示">表示名（英語）</th>
                      <th title="空なら日本語の表示名を辞書で訳して表示">表示名（中国語）</th>
                      <th style={{ width: 44 }}>使用</th>
                      <th style={{ width: 52 }} />
                    </tr>
                  </thead>
                  <tbody>
                    {shown.items.map((it, i) => {
                      const isNew = !!it.isNew;
                      return (
                        <tr key={i} className={it.active ? undefined : 'optm-inactive'}>
                          <td>
                            <button type="button" className="optm-mv" disabled={readOnly || i === 0} onClick={() => move(i, -1)} aria-label="上へ">▲</button>
                            <button type="button" className="optm-mv" disabled={readOnly || i === shown.items.length - 1} onClick={() => move(i, 1)} aria-label="下へ">▼</button>
                          </td>
                          <td>
                            <input
                              className="inp"
                              style={{ width: '100%' }}
                              value={it.code}
                              maxLength={MAX_CODE_LENGTH}
                              readOnly={readOnly || !isNew}
                              placeholder="空なら表示名と同じ"
                              title={isNew ? undefined : '保存済みのコードは変更できません（レポートに保存されている値のため）'}
                              onChange={(e) => patch(i, { code: e.target.value })}
                            />
                          </td>
                          <td>
                            <input className="inp" style={{ width: '100%' }} value={it.label} maxLength={MAX_LABEL_LENGTH} readOnly={readOnly} onChange={(e) => patch(i, { label: e.target.value })} />
                          </td>
                          <td>
                            <input
                              className="inp"
                              lang="en"
                              style={{ width: '100%' }}
                              value={it.labels?.['en'] ?? ''}
                              maxLength={MAX_LABEL_LENGTH}
                              readOnly={readOnly}
                              placeholder={it.label ? tIn('en', it.label) : ''}
                              data-no-i18n=""
                              onChange={(e) => patch(i, { labels: withLabel(it.labels, 'en', e.target.value) })}
                            />
                          </td>
                          <td>
                            <input
                              className="inp"
                              lang="zh-CN"
                              style={{ width: '100%' }}
                              value={it.labels?.['zh-CN'] ?? ''}
                              maxLength={MAX_LABEL_LENGTH}
                              readOnly={readOnly}
                              placeholder={it.label ? tIn('zh-CN', it.label) : ''}
                              data-no-i18n=""
                              onChange={(e) => patch(i, { labels: withLabel(it.labels, 'zh-CN', e.target.value) })}
                            />
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            <input type="checkbox" checked={it.active} disabled={readOnly} onChange={(e) => patch(i, { active: e.target.checked })} title="外すと新しい入力の候補に出なくなる（保存済みのレポートの値は残る）" />
                          </td>
                          <td>{!readOnly && isNew && <Btn small onClick={() => remove(i)}>削除</Btn>}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {!readOnly && (
                <div style={{ marginTop: 4 }}>
                  <Btn small onClick={add}>＋ 追加</Btn>
                  <span className="small" style={{ marginLeft: 8 }}>
                    保存済みの選択値は削除できません。使わなくなった値は「使用」を外してください（過去のレポートでは「（使用停止）」付きで表示されます）。
                  </span>
                </div>
              )}
              {errors.length > 0 && (
                <Note style={{ marginTop: 4 }}>
                  {errors.map((e) => (
                    <div key={e}>{e}</div>
                  ))}
                </Note>
              )}
            </>
          )}
        </div>
      </div>
    </Modal>
  );
}
