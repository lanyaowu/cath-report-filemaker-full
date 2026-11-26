/*
 * mini-react: デモ用 HTML（単一ファイル）を作るための React 互換最小ランタイム。
 * 本番ビルドでは本物の React を使用します（frontend/ を npm で起動）。
 * 対応: 関数コンポーネント / jsx-runtime / useState・useEffect・useMemo・useCallback・useRef・useId・Context / Fragment / createRoot
 */
(function (global) {
  const FRAGMENT = Symbol('Fragment');
  const TEXT = Symbol('Text');
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const SVG_ATTR = { strokeWidth: 'stroke-width', strokeLinecap: 'stroke-linecap', strokeLinejoin: 'stroke-linejoin', strokeDasharray: 'stroke-dasharray', textAnchor: 'text-anchor', fontSize: 'font-size', fontFamily: 'font-family', fillOpacity: 'fill-opacity', fontWeight: 'font-weight' };
  const UNITLESS = new Set(['flex', 'opacity', 'zIndex', 'fontWeight', 'lineHeight', 'flexGrow', 'flexShrink', 'order']);

  function jsx(type, props, key) {
    return { type, props: props || {}, key: key === undefined ? (props && props.key !== undefined ? props.key : null) : key };
  }
  const Fragment = (p) => p.children;
  Fragment.$$frag = true;
  const StrictMode = (p) => p.children;

  // ---------- 正規化 ----------
  function normChildren(c, out = []) {
    if (c == null || c === false || c === true) return out;
    if (Array.isArray(c)) {
      for (const x of c) normChildren(x, out);
      return out;
    }
    if (typeof c === 'string' || typeof c === 'number') out.push({ type: TEXT, props: { text: String(c) }, key: null });
    else out.push(c);
    return out;
  }

  // ---------- フック ----------
  let current = null; // 描画中のコンポーネントインスタンス
  let hookIdx = 0;
  let idCounter = 0;
  const pendingEffects = [];

  function hook() {
    const h = current.hooks;
    if (hookIdx >= h.length) h.push({});
    return h[hookIdx++];
  }
  const depsChanged = (a, b) => !a || !b || a.length !== b.length || a.some((x, i) => !Object.is(x, b[i]));

  function useState(init) {
    const h = hook();
    const inst = current;
    if (!('v' in h)) {
      h.v = typeof init === 'function' ? init() : init;
      h.set = (nv) => {
        const val = typeof nv === 'function' ? nv(h.v) : nv;
        if (Object.is(val, h.v)) return;
        h.v = val;
        schedule(inst);
      };
    }
    return [h.v, h.set];
  }
  function useMemo(f, deps) {
    const h = hook();
    if (!('v' in h) || depsChanged(h.deps, deps)) {
      h.v = f();
      h.deps = deps;
    }
    return h.v;
  }
  const useCallback = (f, deps) => useMemo(() => f, deps);
  function useRef(init) {
    const h = hook();
    if (!('v' in h)) h.v = { current: init };
    return h.v;
  }
  function useId() {
    const h = hook();
    if (!('v' in h)) h.v = `mr${++idCounter}`;
    return h.v;
  }
  function useEffect(f, deps) {
    const h = hook();
    if (depsChanged(h.deps, deps)) {
      h.deps = deps;
      pendingEffects.push(() => {
        if (typeof h.cleanup === 'function') h.cleanup();
        h.cleanup = f();
      });
    }
  }
  function createContext(def) {
    const ctx = { def };
    ctx.Provider = function Provider(p) {
      return p.children;
    };
    ctx.Provider.$$ctx = ctx;
    return ctx;
  }
  function useContext(ctx) {
    let i = current.parent;
    while (i) {
      if (i.type && i.type.$$ctx === ctx) return i.props.value;
      i = i.parent;
    }
    return ctx.def;
  }

  // ---------- DOM ----------
  function setStyle(dom, style) {
    if (typeof style === 'string') {
      dom.style.cssText = style;
      return;
    }
    dom.style.cssText = '';
    for (const k in style || {}) {
      let v = style[k];
      if (v == null || v === '') continue;
      if (typeof v === 'number' && !UNITLESS.has(k)) v = v + 'px';
      const name = k.startsWith('--') ? k : k.replace(/[A-Z]/g, (m) => '-' + m.toLowerCase());
      dom.style.setProperty(name, String(v));
    }
  }
  function eventName(dom, k) {
    if (k === 'onChange') {
      const t = dom.tagName;
      if (t === 'SELECT' || (t === 'INPUT' && (dom.type === 'checkbox' || dom.type === 'radio' || dom.type === 'file'))) return 'change';
      return 'input';
    }
    if (k === 'onDoubleClick') return 'dblclick';
    return k.slice(2).toLowerCase();
  }
  function updateProps(dom, inst, oldP, newP, svg) {
    const all = new Set([...Object.keys(oldP), ...Object.keys(newP)]);
    for (const k of all) {
      if (k === 'children' || k === 'key' || k === 'value' || k === 'checked' || k === 'autoFocus') continue;
      const o = oldP[k];
      const n = newP[k];
      if (k === 'ref') {
        if (n) n.current = dom;
        continue;
      }
      if (k.startsWith('on') && k.length > 2) {
        const ev = eventName(dom, k);
        dom.__h = dom.__h || {};
        if (!dom.__h[ev]) {
          dom.addEventListener(ev, (e) => dom.__h[ev] && dom.__h[ev](e));
        }
        dom.__h[ev] = n;
        continue;
      }
      if (o === n && k !== 'style') continue;
      if (k === 'style') {
        if (JSON.stringify(o) !== JSON.stringify(n)) setStyle(dom, n);
        continue;
      }
      if (k === 'className') {
        if (n) dom.setAttribute('class', n);
        else dom.removeAttribute('class');
        continue;
      }
      if (!svg && (k === 'readOnly' || k === 'disabled' || k === 'hidden' || k === 'multiple' || k === 'selected')) {
        dom[k] = !!n;
        continue;
      }
      const name = k === 'htmlFor' ? 'for' : svg ? SVG_ATTR[k] || k : k;
      if (n == null || (n === false && !k.startsWith('aria-') && !k.startsWith('data-'))) dom.removeAttribute(name);
      else dom.setAttribute(name, n === true && !k.startsWith('aria-') ? '' : String(n));
    }
  }
  function applyValue(dom, p, mounted) {
    if ('value' in p) {
      const v = p.value == null ? '' : String(p.value);
      if (dom.value !== v) dom.value = v;
    }
    if ('checked' in p) dom.checked = !!p.checked;
    if (!mounted && p.autoFocus) setTimeout(() => dom.focus(), 0);
  }

  // ---------- 調停 ----------
  function domNodes(inst, out = []) {
    if (!inst) return out;
    if (inst.dom) out.push(inst.dom);
    else for (const c of inst.kids || []) domNodes(c, out);
    return out;
  }
  function hostParent(inst) {
    let p = inst.parent;
    while (p && !p.dom) p = p.parent;
    return p;
  }
  function arrange(host) {
    const nodes = [];
    for (const c of host.kids) domNodes(c, nodes);
    const parent = host.dom;
    let ref = parent.firstChild;
    for (const n of nodes) {
      if (n === ref) ref = ref.nextSibling;
      else parent.insertBefore(n, ref);
    }
  }
  function unmount(inst, removeDom = true) {
    if (inst.hooks) for (const h of inst.hooks) if (typeof h.cleanup === 'function') h.cleanup();
    for (const c of inst.kids || []) unmount(c, false);
    inst.dead = true;
    if (removeDom) for (const n of domNodes(inst)) n.parentNode && n.parentNode.removeChild(n);
  }
  const sameType = (inst, v) => inst && inst.type === v.type && inst.key === v.key;

  function reconcile(parent, inst, vnode, svg) {
    if (inst && !sameType(inst, vnode)) {
      unmount(inst);
      inst = null;
    }
    const t = vnode.type;
    if (t === TEXT) {
      if (!inst) inst = { type: TEXT, key: vnode.key, parent, dom: document.createTextNode(vnode.props.text), props: vnode.props };
      else if (inst.props.text !== vnode.props.text) inst.dom.nodeValue = vnode.props.text;
      inst.props = vnode.props;
      return inst;
    }
    if (typeof t === 'string') {
      const isSvg = svg || t === 'svg';
      const mounted = !!inst;
      if (!inst) inst = { type: t, key: vnode.key, parent, dom: isSvg ? document.createElementNS(SVG_NS, t) : document.createElement(t), props: {}, kids: [] };
      inst.parent = parent;
      updateProps(inst.dom, inst, inst.props, vnode.props, isSvg);
      inst.kids = reconcileKids(inst, inst.kids, normChildren(vnode.props.children), isSvg && t !== 'foreignObject');
      arrange(inst);
      applyValue(inst.dom, vnode.props, mounted);
      inst.props = vnode.props;
      return inst;
    }
    // コンポーネント
    if (!inst) inst = { type: t, key: vnode.key, parent, hooks: [], kids: [], svg };
    inst.parent = parent;
    inst.props = vnode.props;
    inst.svg = svg;
    renderComponent(inst);
    return inst;
  }
  function renderComponent(inst) {
    const prev = current;
    const prevIdx = hookIdx;
    current = inst;
    hookIdx = 0;
    let out;
    try {
      out = inst.type(inst.props);
    } finally {
      current = prev;
      hookIdx = prevIdx;
    }
    inst.dirty = false;
    inst.kids = reconcileKids(inst, inst.kids, normChildren(out), inst.svg);
  }
  function reconcileKids(parent, oldKids, vkids, svg) {
    const keyed = new Map();
    oldKids.forEach((k, i) => keyed.set(k.key != null ? 'k:' + k.key : 'i:' + i, k));
    const used = new Set();
    const res = vkids.map((v, i) => {
      const id = v.key != null ? 'k:' + v.key : 'i:' + i;
      let old = keyed.get(id);
      if (old && !sameType(old, v)) old = undefined;
      if (old) used.add(old);
      return reconcile(parent, old, v, svg);
    });
    for (const k of oldKids) if (!used.has(k) && !res.includes(k)) unmount(k);
    return res;
  }

  // ---------- スケジューラ ----------
  const dirty = new Set();
  let scheduled = false;
  function depth(i) {
    let d = 0;
    while (i) {
      d++;
      i = i.parent;
    }
    return d;
  }
  function schedule(inst) {
    dirty.add(inst);
    if (!scheduled) {
      scheduled = true;
      Promise.resolve().then(flush);
    }
  }
  function flush() {
    scheduled = false;
    const list = [...dirty].sort((a, b) => depth(a) - depth(b));
    dirty.clear();
    for (const inst of list) {
      if (inst.dead) continue;
      let anc = inst.parent;
      let covered = false;
      while (anc) {
        if (list.includes(anc) && !anc.dead) {
          covered = true;
          break;
        }
        anc = anc.parent;
      }
      if (covered) continue;
      renderComponent(inst);
      const host = hostParent(inst);
      if (host) arrange(host);
    }
    runEffects();
  }
  function runEffects() {
    while (pendingEffects.length) {
      const e = pendingEffects.splice(0);
      setTimeout(() => e.forEach((f) => f()), 0);
    }
  }

  function createRoot(el) {
    const root = { type: 'root', dom: el, kids: [], props: {} };
    return {
      render(v) {
        root.kids = reconcileKids(root, root.kids, normChildren(v), false);
        arrange(root);
        runEffects();
      },
    };
  }

  const React = { useState, useEffect, useMemo, useCallback, useRef, useId, useContext, createContext, Fragment, StrictMode };
  global.__miniReact = { React, jsxRuntime: { jsx, jsxs: jsx, Fragment }, dom: { createRoot } };
})(window);
