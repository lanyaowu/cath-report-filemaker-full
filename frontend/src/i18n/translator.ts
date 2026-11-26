/**
 * 画面の多言語表示（日本語 ⇔ 簡体字中国語）。React 版・Thymeleaf 版で同じコードを使う
 * （Thymeleaf 版の static/js/i18n.js は、このファイルを tools/i18n/build-tl.mjs で変換したもの）。
 *
 * 仕組み：
 * - 画面の文言は日本語のまま書き、表示する直前に DOM の文字（テキスト・title・placeholder 等）を辞書で置き換える。
 *   画面ごとのコードを書き換えずに済み、保存する値（コード・入力値・option の value）は日本語のまま変わらない。
 * - 辞書は「完全一致」と「パターン（{} が可変部分）」の 2 種類。前後の空白・改行は無視して照合する。
 * - MutationObserver で React の再描画・Thymeleaf 版の JS による書き換えも追いかける。
 * - 日本語に戻すと、覚えておいた元の文字に戻す。
 * - 翻訳しない部分には data-no-i18n を付ける（入力値・患者名などは input の value なので元々対象外）。
 */

export type Lang = 'ja' | 'en' | 'zh-CN';
/** 切替に出す言語（表示名はその言語の表記） */
export const LANGS: { code: Lang; label: string }[] = [
  { code: 'ja', label: '日本語' },
  { code: 'en', label: 'English' },
  { code: 'zh-CN', label: '中文' },
];
export const isLang = (v: unknown): v is Lang => v === 'ja' || v === 'en' || v === 'zh-CN';

export interface Dictionary {
  lang: string;
  exact: Record<string, string>;
  /** [日本語, 訳]。{} は可変部分（順番どおりに置き換える） */
  patterns: [string, string][];
}

interface Compiled {
  re: RegExp;
  /** 照合を速くするための、パターンの中で一番長い固定部分 */
  hint: string;
  out: string[];
}

/** 1 言語分の辞書を照合しやすい形にしたもの */
interface Engine {
  exact: Map<string, string>;
  compiled: Compiled[];
  cache: Map<string, string>;
  /** 並べた語句の区切り（英語は「、」を「, 」にする） */
  sep: (s: string) => string;
}

function compile(dict: Dictionary, lang: Lang): Engine {
  const compiled: Compiled[] = dict.patterns.map(([ja, tr]) => {
    const parts = ja.split('{}');
    const fixed = parts.join('');
    // 固定部分が短いパターン（「{}歳」など）は、可変部分を数値に限る（誤訳を防ぐ）
    const cap = fixed.replace(/\s/g, '').length <= 2 ? '([0-9０-９.,\\-〜~/ ]+)' : '(.+?)';
    return {
      re: new RegExp('^' + parts.map((p) => esc(p).replace(/ /g, '\\s*')).join(cap) + '$'),
      hint: [...parts].sort((a, b) => b.trim().length - a.trim().length)[0].trim(),
      out: tr.split('{}'),
    };
  });
  const EN_SEP: Record<string, string> = { '、': ', ', '・': ' / ', '／': ' / ', '，': ', ' };
  return {
    exact: new Map(Object.entries(dict.exact)),
    compiled,
    cache: new Map(),
    sep: lang === 'en' ? (x) => EN_SEP[x.trim()] ?? x : (x) => x,
  };
}

const ATTRS = ['title', 'placeholder', 'aria-label', 'alt'] as const;
const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'NOSCRIPT', 'CODE', 'PRE']);
const JA = /[぀-ヿ㐀-鿿]/;
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export const normalize = (s: string) => s.replace(/\s+/g, ' ').trim();

/**
 * @param dicts 言語ごとの辞書（日本語は不要。無い言語は日本語のまま表示）
 */
export function createTranslator(dicts: Partial<Record<Lang, Dictionary>>) {
  let lang: Lang = 'ja';
  const engines = new Map<Lang, Engine>();
  const engine = (): Engine | undefined => {
    if (lang === 'ja') return undefined;
    let e = engines.get(lang);
    if (!e && dicts[lang]) engines.set(lang, (e = compile(dicts[lang]!, lang)));
    return e;
  };
  let E: Engine = compile({ lang: 'ja', exact: {}, patterns: [] }, 'ja');

  /** 1 行分（前後の空白は残す） */
  const line = (s: string): string => {
    const n = normalize(s);
    if (!n || !JA.test(n)) return s;
    let out = E.cache.get(n);
    if (out === undefined) {
      // 並べた語句が全部訳せるなら、パターンより先に語句ごとに訳す（「透視 22分、総線量 1303mGy」がパターン「透視 {}mGy」に誤って当たらないように）
      out = E.exact.get(n) ?? listed(n, true) ?? matchPattern(n) ?? wrapped(n) ?? listed(n, false) ?? n;
      E.cache.set(n, out);
    }
    if (out === n) return s;
    const lead = /^\s*/.exec(s)![0];
    const trail = /\s*$/.exec(s)![0];
    return lead + out + trail;
  };

  const matchPattern = (n: string): string | undefined => {
    for (const c of E.compiled) {
      if (c.hint && !n.includes(c.hint)) continue;
      const m = c.re.exec(n);
      if (!m) continue;
      // 可変部分も辞書にあれば訳す（「選択値「入力中」を保存しました」の「入力中」など）
      return c.out.reduce((acc, z, i) => acc + (i === 0 ? '' : sub(m[i] ?? '')) + z, '');
    }
    return undefined;
  };
  const sub = (v: string) => E.exact.get(normalize(v)) ?? v;
  /** 1 つの語句（完全一致・パターン・記号で囲まれた語句） */
  const one = (v: string): string | undefined => E.exact.get(v) ?? matchPattern(v) ?? wrapped(v);
  /** 「、」「・」「／」で並べた文言（検査報告書の「HT、喫煙（過去）、家族歴」など）は、語句ごとに訳す */
  const listed = (n: string, all: boolean): string | undefined => {
    const parts = n.split(/([、・／，]\s*)/);
    if (parts.length < 3) return undefined;
    let changed = false;
    let missed = false;
    const out = parts.map((p, i) => {
      if (i % 2 === 1) return E.sep(p);
      if (!p.trim()) return p;
      const z = one(p.trim());
      if (z === undefined) {
        if (JA.test(p)) missed = true;
        return p;
      }
      changed = true;
      return p.replace(p.trim(), z);
    });
    return changed && !(all && missed) ? out.join('') : undefined;
  };
  /** 記号・空白で囲まれた文言（「＋ 側副血行を追加」「● 未保存」など）は、中身だけ辞書で訳す */
  const wrapped = (n: string): string | undefined => {
    const m = /^([^\p{L}\p{N}]*)(.*?)([^\p{L}\p{N}]*)$/u.exec(n);
    if (!m || (!m[1] && !m[3])) return undefined;
    const z = E.exact.get(m[2].trim());
    return z === undefined ? undefined : m[1] + z + m[3];
  };

  /** 文字列の翻訳（改行を含むメッセージは行ごと） */
  const t = (s: string | null | undefined): string => {
    if (s == null) return '';
    if (lang === 'ja' || !engine() || !JA.test(s)) return s;
    E = engine()!;
    return s.includes('\n') ? s.split('\n').map(line).join('\n') : line(s);
  };

  // ---- DOM ----
  const textOrig = new WeakMap<Text, { orig: string; shown: string }>();
  const attrOrig = new WeakMap<Element, Map<string, { orig: string; shown: string }>>();

  /** 翻訳しない要素（data-no-i18n の中・編集できる領域） */
  const skip = (el: Element | null): boolean => {
    for (let e = el; e; e = e.parentElement) {
      if (e.hasAttribute('data-no-i18n') || (e as HTMLElement).isContentEditable) return true;
    }
    return false;
  };
  /** 文字を訳さない要素（script・textarea の中身など。title などの属性は訳す） */
  const skipText = (parent: Element | null): boolean => !parent || SKIP_TAGS.has(parent.tagName) || skip(parent);

  const doText = (node: Text) => {
    const cur = node.nodeValue ?? '';
    const rec = textOrig.get(node);
    // 表示中の訳と違う = 画面側で書き換えられた → 新しい日本語を元の文字として覚え直す
    const orig = rec && rec.shown === cur ? rec.orig : cur;
    const shown = t(orig);
    if (shown !== cur) node.nodeValue = shown;
    if (shown !== orig || rec) textOrig.set(node, { orig, shown });
  };

  const doAttrs = (el: Element) => {
    const names: string[] = [...ATTRS];
    if (el.tagName === 'INPUT' && /^(button|submit|reset)$/i.test((el as HTMLInputElement).type)) names.push('value');
    for (const a of names) {
      if (!el.hasAttribute(a)) continue;
      const cur = el.getAttribute(a) ?? '';
      let m = attrOrig.get(el);
      const rec = m?.get(a);
      const orig = rec && rec.shown === cur ? rec.orig : cur;
      const shown = t(orig);
      if (shown !== cur) el.setAttribute(a, shown);
      if (shown !== orig || rec) {
        if (!m) attrOrig.set(el, (m = new Map()));
        m.set(a, { orig, shown });
      }
    }
  };

  const walk = (root: Node) => {
    if (root.nodeType === 3) {
      if (!skipText(root.parentElement)) doText(root as Text);
      return;
    }
    if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) return;
    if (root.nodeType === 1 && skip(root as Element)) return;
    if (root.nodeType === 1) doAttrs(root as Element);
    const doc = root.ownerDocument ?? (root as Document);
    const w = doc.createTreeWalker(root, 1 | 4, {
      acceptNode: (n) => (n.nodeType === 1 && ((n as Element).hasAttribute('data-no-i18n') || (n as HTMLElement).isContentEditable) ? 2 /* REJECT */ : 1 /* ACCEPT */),
    });
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      if (n.nodeType === 3) {
        if (!SKIP_TAGS.has(n.parentElement?.tagName ?? '')) doText(n as Text);
      } else doAttrs(n as Element);
    }
  };

  let observer: MutationObserver | undefined;
  let titleOrig: string | undefined;

  const apply = (doc: Document = document) => {
    if (titleOrig === undefined) titleOrig = doc.title;
    doc.title = t(titleOrig);
    doc.documentElement.lang = lang;
    if (doc.body) walk(doc.body);
  };

  /** 画面の変化を追いかけて翻訳する（日本語の時は何もしない） */
  const observe = (doc: Document = document) => {
    if (observer || typeof MutationObserver === 'undefined') return;
    observer = new MutationObserver((list) => {
      if (lang === 'ja') return;
      for (const m of list) {
        if (m.type === 'characterData') {
          const n = m.target as Text;
          if (!skipText(n.parentElement)) doText(n);
        } else if (m.type === 'attributes') {
          const el = m.target as Element;
          if (!skip(el)) doAttrs(el);
        } else m.addedNodes.forEach((n) => walk(n));
      }
    });
    observer.observe(doc.documentElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: [...ATTRS, 'value'],
    });
  };

  /** 日本語へ戻す（覚えておいた元の文字に戻す） */
  const restore = (doc: Document = document) => {
    const w = doc.createTreeWalker(doc.body, 1 | 4);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      if (n.nodeType === 3) {
        const rec = textOrig.get(n as Text);
        if (rec && rec.shown === n.nodeValue) n.nodeValue = rec.orig;
        textOrig.delete(n as Text);
      } else {
        const m = attrOrig.get(n as Element);
        m?.forEach((rec, a) => {
          if ((n as Element).getAttribute(a) === rec.shown) (n as Element).setAttribute(a, rec.orig);
        });
        attrOrig.delete(n as Element);
      }
    }
    if (titleOrig !== undefined) doc.title = titleOrig;
    titleOrig = undefined;
    doc.documentElement.lang = 'ja';
  };

  let dialogsPatched = false;
  /** confirm / alert / prompt の文言も訳す */
  const patchDialogs = (win: Window = window) => {
    if (dialogsPatched) return;
    dialogsPatched = true;
    const c = win.confirm.bind(win);
    const a = win.alert.bind(win);
    const p = win.prompt.bind(win);
    win.confirm = (m?: string) => c(t(m));
    win.alert = (m?: unknown) => a(typeof m === 'string' ? t(m) : m);
    win.prompt = (m?: string, d?: string) => p(t(m), d);
  };

  return {
    t,
    get lang() {
      return lang;
    },
    setLang(next: Lang, doc: Document = document) {
      if (next === lang) return;
      const prev = lang;
      lang = next;
      if (next === 'ja') restore(doc);
      else {
        if (prev !== 'ja') restore(doc);
        apply(doc);
        observe(doc);
      }
    },
    /** 文字列の翻訳に使う言語だけを選ぶ（DOM は触らない） */
    select(l: Lang) {
      lang = l;
    },
    /** 起動時：言語を決めて画面を翻訳し、以後の変化を追いかける */
    start(initial: Lang, doc: Document = document) {
      patchDialogs(doc.defaultView ?? window);
      lang = initial;
      doc.documentElement.lang = initial;
      if (initial !== 'ja') {
        apply(doc);
        observe(doc);
      }
    },
    apply,
  };
}

export type Translator = ReturnType<typeof createTranslator>;
