import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';
import { i18n, savedLang } from './i18n';

// 画面の言語（日本語・中文）。描画より先に始め、以後の描画は MutationObserver で翻訳する
i18n.start(savedLang());

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
