import { useState } from 'react';
import { Tabs } from '../../components/common/ui';

type Site = 'pmL' | 'pmR' | 'dm' | 'dmC' | 'sbC' | 'sb';
const PLAQUE: Record<Site, [number, number, number]> = {
  pmL: [28, 34, 13], // proximal main 外側
  pmR: [56, 26, 13], // proximal main 内側（カリナ対側）
  dm: [30, 82, 11], // distal main 外側
  dmC: [52, 74, 9], // distal main カリナ側
  sbC: [66, 66, 9], // side branch 入口
  sb: [86, 78, 9], // side branch 遠位
};

/** 分岐部の模式図（本アプリ独自の簡易図） */
function Bif({ sites, stents, label, caption }: { sites: Site[]; stents?: ('main' | 'side' | 'prox')[]; label?: string; caption?: string }) {
  const id = `dots-${sites.join('')}-${(stents ?? []).join('')}-${label ?? ''}`.replace(/[^A-Za-z0-9_-]/g, '_');
  return (
    <figure className="bif">
      <svg viewBox="0 0 120 112" width={140} height={130}>
        <defs>
          <pattern id={id} width={4} height={4} patternUnits="userSpaceOnUse">
            <circle cx={2} cy={2} r={0.9} fill="#222" />
          </pattern>
        </defs>
        <path d="M16,6 L58,6 L64,52 L112,82 L102,100 L58,74 L52,108 L24,108 Z" fill="#fff" stroke="#111" strokeWidth={2} strokeLinejoin="round" />
        {stents?.includes('prox') && <rect x={22} y={10} width={30} height={42} fill="none" stroke="#2a7bd8" strokeWidth={2} strokeDasharray="3 2" />}
        {stents?.includes('main') && <rect x={22} y={10} width={30} height={94} fill="none" stroke="#2a7bd8" strokeWidth={2} strokeDasharray="3 2" />}
        {stents?.includes('side') && <polygon points="56,58 66,52 108,82 100,94" fill="none" stroke="#d8542a" strokeWidth={2} strokeDasharray="3 2" />}
        {sites.map((s) => {
          const [x, y, r] = PLAQUE[s];
          return <circle key={s} cx={x} cy={y} r={r} fill={`url(#${id})`} stroke="#111" strokeWidth={0.8} />;
        })}
      </svg>
      {label && <figcaption className="bif-label">{label}</figcaption>}
      {caption && <figcaption className="bif-cap">{caption}</figcaption>}
    </figure>
  );
}

const TYPES: { k: string; sites: Site[]; cap: string }[] = [
  { k: 'a', sites: ['pmL', 'pmR'], cap: 'proximal main' },
  { k: 'b', sites: ['pmL', 'pmR', 'dm'], cap: '+ distal main br.' },
  { k: 'c', sites: ['pmL', 'pmR', 'sbC'], cap: '+ side br.' },
  { k: 'd', sites: ['pmL', 'pmR', 'dm', 'sbC'], cap: '+ distal main br. + side br.' },
  { k: 'e', sites: ['dm', 'dmC'], cap: 'distal main' },
  { k: 'f', sites: ['dm', 'dmC', 'sbC'], cap: 'distal main + side br.' },
  { k: 'g', sites: ['sbC', 'sb'], cap: 'side br. only' },
];

const MEDINA: { code: string; sites: Site[] }[] = [
  { code: '1,1,1', sites: ['pmR', 'dmC', 'sbC'] },
  { code: '1,1,0', sites: ['pmR', 'dmC'] },
  { code: '1,0,1', sites: ['pmR', 'sbC'] },
  { code: '0,1,1', sites: ['dmC', 'sbC'] },
  { code: '1,0,0', sites: ['pmR'] },
  { code: '0,1,0', sites: ['dmC'] },
  { code: '0,0,1', sites: ['sbC'] },
];

const STRATEGIES: { name: string; stents: ('main' | 'side' | 'prox')[]; text: string }[] = [
  { name: 'Provisional', stents: ['main'], text: '本幹にステント留置。側枝は必要時のみ追加治療（KBT/POT）。第一選択となることが多い。' },
  { name: 'T-stent / TAP', stents: ['main', 'side'], text: '側枝入口部に最小限の突出でステントを留置し、本幹ステントと T 字に組み合わせる。' },
  { name: 'Culotte', stents: ['prox', 'main', 'side'], text: '近位部で2本のステントを重ね、本幹と側枝それぞれへ展開する。' },
  { name: 'Crush / DK-crush', stents: ['main', 'side'], text: '側枝ステントの近位端を本幹ステントで圧着。DK-crush は途中で KBT を追加する。' },
  { name: 'V-stent / SKS', stents: ['main', 'side'], text: '2本のステントを同時に展開し、近位でV字または新カリナを形成する。' },
];

/** 参考資料タブ（分岐部病変タイプ / 分岐部治療ストラテジー / Medina分類） */
export function ReferenceTab() {
  const [tab, setTab] = useState('type');
  return (
    <div className="reference">
      <Tabs
        small
        active={tab}
        onChange={setTab}
        tabs={[
          { key: 'type', label: '分岐部病変タイプ' },
          { key: 'strategy', label: '分岐部治療ストラテジー' },
          { key: 'medina', label: 'Medina分類' },
        ]}
      />
      <div className="ref-body">
        {tab === 'type' && (
          <>
            <div className="ref-card">
              <div className="ref-row">
                <div className="ref-side">proximal<br />main<br />branch</div>
                {TYPES.slice(0, 4).map((t) => (
                  <Bif key={t.k} sites={t.sites} label={t.k} caption={t.cap} />
                ))}
              </div>
              <div className="ref-row">
                <div className="ref-side">distal<br />main<br />branch</div>
                {TYPES.slice(4).map((t) => (
                  <Bif key={t.k} sites={t.sites} label={t.k} caption={t.cap} />
                ))}
              </div>
            </div>
            <div className="ref-text">
              ●分岐部病変タイプ<br />
              Type a〜d：側枝分岐の直近位部に50%以上の狭窄を有するもの。Type e〜g：遠位主枝または側枝入口部に50%以上の狭窄を有するもの。
            </div>
          </>
        )}
        {tab === 'strategy' && (
          <div className="ref-card">
            <div className="ref-row wrap">
              {STRATEGIES.map((s) => (
                <div key={s.name} className="strategy">
                  <Bif sites={[]} stents={s.stents} label={s.name} />
                  <p>{s.text}</p>
                </div>
              ))}
            </div>
            <div className="ref-text">青破線：本幹ステント　赤破線：側枝ステント</div>
          </div>
        )}
        {tab === 'medina' && (
          <div className="ref-card">
            <div className="ref-row wrap">
              {MEDINA.map((m) => (
                <Bif key={m.code} sites={m.sites} label={`Medina ${m.code}`} />
              ))}
            </div>
            <div className="ref-text">
              ●Medina分類：近位主枝, 遠位主枝, 側枝 の順に、50%以上の狭窄があれば 1、なければ 0 と表記する。1,1,1 / 1,0,1 / 0,1,1 は真の分岐部病変（true bifurcation）。
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
