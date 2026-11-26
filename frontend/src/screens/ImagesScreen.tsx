import { useMemo, useRef, useState } from 'react';
import { useApp } from '../state/AppContext';
import { Scope, useVal } from '../form/FormContext';
import { CheckF, DateF, SelectF, TextAreaF, TextF } from '../form/fields';
import { Btn, Empty, Modal, Panel, Row } from '../components/common/ui';
import { ScreenFrame } from '../components/layout/ScreenFrame';
import { IMAGE_CATEGORIES, IMAGE_VIEWS } from '../constants/options';
import { useOptionList } from '../form/OptionsContext';
import { createImageItem } from '../model/defaults';
import { fmtDate } from '../utils/date';
import type { ImageItem } from '../types/model';

const MAX_BYTES = 1_500_000; // LocalStorage 容量を考慮した上限

/** 画像データが無い場合のプレースホルダ */
function placeholder(item: ImageItem) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="320" height="240" fill="#30383d"/><text x="160" y="115" font-size="22" fill="#cfd8dc" text-anchor="middle" font-family="sans-serif">${item.category || 'IMAGE'}</text><text x="160" y="145" font-size="12" fill="#90a4ae" text-anchor="middle" font-family="sans-serif">${item.view || ''}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

/** 画像（参考画面なし：シネ・心電図・X-P・IVUS 等の画像管理として推測） */
export function ImagesScreen() {
  const app = useApp();
  const images = useVal<ImageItem[]>('/report.images');
  const [sel, setSel] = useState(0);
  const [cat, setCat] = useState('');
  const imageCategories = useOptionList(IMAGE_CATEGORIES);
  const [viewer, setViewer] = useState<ImageItem | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const shown = useMemo(() => images.map((im, i) => ({ im, i })).filter(({ im }) => !cat || im.category === cat), [images, cat]);
  const cur = images[sel] ? sel : -1;

  const setImages = (v: ImageItem[]) => app.form!.set('report.images', v);

  const onFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    const added: ImageItem[] = [];
    for (const f of Array.from(files)) {
      if (f.size > MAX_BYTES) {
        app.toast(`${f.name}: 1.5MB を超える画像は登録できません`, 'err');
        continue;
      }
      const dataUrl = await new Promise<string>((res, rej) => {
        const r = new FileReader();
        r.onload = () => res(String(r.result));
        r.onerror = () => rej(r.error);
        r.readAsDataURL(f);
      });
      const cat0 = f.type.includes('dicom') ? 'Cine' : 'Other';
      added.push({ ...createImageItem(), fileName: f.name, mimeType: f.type, dataUrl, title: f.name.replace(/\.[^.]+$/, ''), takenAt: app.draft!.report.header.studyDate, category: cat0 });
    }
    if (added.length) {
      setImages([...images, ...added]);
      setSel(images.length);
    }
    if (fileRef.current) fileRef.current.value = '';
  };

  const remove = (i: number) =>
    app.confirm({
      title: '画像削除',
      message: `「${images[i].title || images[i].fileName}」を削除します（保存で確定）。`,
      danger: true,
      okLabel: '削除',
      onOk: () => {
        setImages(images.filter((_, j) => j !== i));
        setSel(Math.max(0, i - 1));
      },
    });

  return (
    <ScreenFrame>
      <div className="images-layout">
        <Panel
          title={`画像一覧（${images.length}件）`}
          right={
            <Row>
              <select className="inp" value={cat} onChange={(e) => setCat(e.target.value)}>
                <option value="">全種別</option>
                {imageCategories.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
              <Btn small kind="primary" onClick={() => fileRef.current?.click()}>＋ 画像追加</Btn>
              <input ref={fileRef} type="file" accept="image/*" multiple hidden onChange={(e) => void onFiles(e.target.files)} />
            </Row>
          }
        >
          {shown.length === 0 ? (
            <Empty>画像がありません。「画像追加」から登録できます。</Empty>
          ) : (
            <div className="thumbs">
              {shown.map(({ im, i }) => (
                <button key={im.id} type="button" className={`thumb ${i === cur ? 'sel' : ''}`} onClick={() => setSel(i)} onDoubleClick={() => setViewer(im)}>
                  <img src={im.dataUrl || placeholder(im)} alt={im.title} />
                  <div className="thumb-cap">
                    {im.keyImage && <span className="key">★</span>}
                    <span className="cat">{im.category}</span> {im.title}
                  </div>
                  <div className="thumb-sub">
                    {fmtDate(im.takenAt)} {im.view} {im.lesion}
                  </div>
                </button>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="画像情報" className="image-detail">
          {cur < 0 ? (
            <Empty>画像を選択してください</Empty>
          ) : (
            <Scope path={`/report.images.${cur}`} key={images[cur].id}>
              <img className="detail-img" src={images[cur].dataUrl || placeholder(images[cur])} alt="" onClick={() => setViewer(images[cur])} />
              <TextF path="title" label="タイトル" lw={70} w={220} />
              <SelectF path="category" label="種別" lw={70} w={120} options={IMAGE_CATEGORIES} />
              <DateF path="takenAt" label="撮影日" lw={70} />
              <TextF path="view" label="撮影方向" lw={70} w={140} list={IMAGE_VIEWS} />
              <TextF path="lesion" label="対象病変" lw={70} w={140} list={app.draft!.report.pci.lesions.map((l) => l.target).filter(Boolean)} />
              <TextAreaF path="description" label="所見" lw={70} rows={3} />
              <CheckF path="keyImage" label="キー画像（報告書に掲載）" />
              <div className="muted small">ファイル: {images[cur].fileName || '-'} {images[cur].mimeType}</div>
              <Row style={{ marginTop: 6 }}>
                <Btn small onClick={() => setViewer(images[cur])}>拡大表示</Btn>
                <Btn small kind="danger" onClick={() => remove(cur)}>削除</Btn>
              </Row>
            </Scope>
          )}
        </Panel>
      </div>
      {viewer && (
        <Modal title={viewer.title || viewer.fileName} onClose={() => setViewer(null)} width="80vw">
          <img src={viewer.dataUrl || placeholder(viewer)} alt="" style={{ width: '100%', maxHeight: '70vh', objectFit: 'contain', background: '#000' }} />
          <p>{viewer.description}</p>
        </Modal>
      )}
    </ScreenFrame>
  );
}
