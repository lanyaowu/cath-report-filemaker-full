"""心カテレポートシステムの説明資料（仕組み・概要・主な機能・データモデル・特徴・ワークフロー・良いところと改善）
usage: python3 tools/design_doc/doc_explain.py
"""
import subprocess
from extra_common import G, e, table, build_doc, RELATED
import doc_summary as S

IMG = G.ROOT / 'docs/design/img'
SHOT = G.ROOT / 'demo/screenshots'
FONT = 'Noto Sans CJK JP'


def dot(name, src):
    subprocess.run(['dot', '-Tsvg', '-o', str(IMG / f'{name}.svg')], input=src.encode('utf-8'), check=True)


def fig(name, cap, h='95mm'):
    return (f'<div class="fig"><img src="{(IMG / (name + ".svg")).as_uri()}" style="width:100%;max-height:{h};object-fit:contain"></div>'
            f'<p class="cap">{e(cap)}</p>')


def shot(fn, cap, w='100%'):
    return (f'<div class="fig"><img src="{(SHOT / fn).as_uri()}" style="width:{w};border:1px solid #c9d3d6"></div>'
            f'<p class="cap">{e(cap)}</p>')


def two_shots(a, ca, b, cb):
    cell = lambda fn, c: (f'<td style="width:50%;vertical-align:top;border:0;padding:0 2mm"><img src="{(SHOT / fn).as_uri()}" '
                          f'style="width:100%;border:1px solid #c9d3d6"><p class="cap">{e(c)}</p></td>')
    return f'<table style="width:100%;border:0"><tr>{cell(a, ca)}{cell(b, cb)}</tr></table>'


# ------------------------------------------------------------------ 図
def make_figs():
    dot('ex_system', f'''digraph G {{
  graph [rankdir=TB, fontname="{FONT}", nodesep=0.5, ranksep=0.45, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=15, fillcolor="#eef5f2", color="#5d8a7c", margin="0.2,0.1"];
  edge [fontname="{FONT}", fontsize=13, color="#5b6f75", fontcolor="#44585e"];
  users [label="利用者\\n医師・秘書・管理者・閲覧", shape=folder, fillcolor="#fdf6e3", color="#c9a54b"];
  subgraph cluster_r {{ label="React 版"; fontname="{FONT}"; fontsize=15; style="rounded"; color="#5b84b1";
    rui [label="ブラウザ\\nReact + TypeScript\\n（画面・計算・変更検知）", fillcolor="#e6f0fa", color="#5b84b1"];
    ls [label="Local Storage\\n（デモ・試用）", fillcolor="#f1f1f1", color="#999999"];
    api [label="REST API\\nNode.js / Spring Boot\\n（認証・権限・業務ルール）", fillcolor="#e6f0fa", color="#5b84b1"];
    rui -> ls [label="保存先を選択", style=dashed];
    rui -> api [label="JSON（トークン）"]; }}
  subgraph cluster_t {{ label="Thymeleaf 版"; fontname="{FONT}"; fontsize=15; style="rounded"; color="#d8a25e";
    tui [label="ブラウザ\\nHTML + JavaScript\\n（変更検知・計算）", fillcolor="#fdf1e2", color="#d8a25e"];
    tsv [label="Spring Boot + Thymeleaf\\n（画面生成・認証・権限・\\n業務ルール）", fillcolor="#fdf1e2", color="#d8a25e"];
    tui -> tsv [label="画面 / 保存（セッション）"]; }}
  db1 [label="MongoDB\\n（患者・レポート・マスタ）", shape=cylinder, fillcolor="#f3e8f7", color="#9b6bb3"];
  db2 [label="PostgreSQL\\n（列＋JSONB・画像・監査ログ）", shape=cylinder, fillcolor="#f3e8f7", color="#9b6bb3"];
  users -> rui; users -> tui;
  api -> db1; api -> db2; tsv -> db2;
}}''')
    dot('ex_model', f'''digraph G {{
  graph [rankdir=TB, fontname="{FONT}", nodesep=0.25, ranksep=0.5, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=14, fillcolor="#eef5f2", color="#5d8a7c", margin="0.14,0.08"];
  edge [fontname="{FONT}", fontsize=12, color="#5b6f75", fontcolor="#44585e", arrowhead=none];
  pt [label="患者 Patient\\nID・氏名・生年月日\\n既往・感染症", fillcolor="#fdf6e3", color="#c9a54b"];
  rp [label="レポート CathReport（1 検査）\\nヘッダ・状態（入力中/確定）\\n照合・登録履歴", fillcolor="#fdf1e2", color="#d8a25e", penwidth=1.6];
  ms [label="マスタ\\n医師・施設・デバイス", fillcolor="#f1f1f1", color="#999999"];
  pt -> rp [label="1 : N", arrowhead=crow];
  subgraph cluster_s {{ label="レポートの中身（画面ごとのセクション）"; fontname="{FONT}"; fontsize=13; style="rounded,dashed"; color="#9fb7c9";
    cr [label="カテ記録\\n検査情報・術者\\nHemodynamics\\n検査値・既往歴・合併症"];
    cg [label="CAG/LVG\\nセグメント所見\\n側副血行[1..5]\\nグラフト[1..4]・LVG"];
    pc [label="PCI\\n基本（デバイス）\\n病変[1..5]\\nJ-PCI・リスク・AMI"];
    pi [label="Pressure/IVUS\\nPressure Wire[1..5]\\n＝ IVUS Lesion[1..5]"];
    ot [label="PCPS\\nカンファレンス\\nMACE[5]・画像[ ]\\nRestudy"]; }}
  rp -> cr; rp -> cg; rp -> pc; rp -> pi; rp -> ot;
  ms -> rp [style=dotted, label="入力の候補", arrowhead=vee];
  {{ rank=same; rp; ms; }}
  edge [style=dashed, color="#2b6cb0", fontcolor="#2b6cb0", arrowhead=vee, constraint=false];
  pi -> pc [label="QCA 取得"];
  cg -> pc [label="Target の候補"];
}}''')
    dot('ex_flow', f'''digraph G {{
  graph [rankdir=TB, fontname="{FONT}", nodesep=0.3, ranksep=0.45, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=14, fillcolor="#eef5f2", color="#5d8a7c", margin="0.12,0.08", width=1.9, height=0.95];
  edge [color="#5b6f75", arrowsize=0.8];
  a [label="① ログイン", fillcolor="#e9eef0", color="#7f939c"];
  b [label="② 新規作成\\n患者を選ぶ・登録"];
  c [label="③ カテ記録\\n検査情報・術者・時刻\\n検査値・既往歴"];
  d [label="④ CAG/LVG\\n狭窄所見・病変枝\\nEF"];
  e [label="⑤ PCI\\n病変（Target）・Device\\n成否・J-PCI"];
  f [label="⑥ Pressure/IVUS\\n画像\\n（必要な時）"];
  g [label="⑦ 保存\\n確定前の確認"];
  h [label="⑧ 確定・照合", fillcolor="#fdf1e2", color="#d8a25e"];
  i [label="⑨ 検査報告書\\nカンファレンス", fillcolor="#e6f0fa", color="#5b84b1"];
  j [label="⑩ 経過観察\\nMACE・Restudy", fillcolor="#f3e8f7", color="#9b6bb3"];
  {{ rank=same; a; b; c; d; e; }}
  {{ rank=same; f; g; h; i; j; }}
  a -> b -> c -> d -> e;
  f -> g -> h -> i -> j;
  e -> f [constraint=false];
  a -> f [style=invis];
}}''')


# ------------------------------------------------------------------ 本文
def p_overview():
    mech = [
        ('1 件のレポート', '1 回の検査を 1 件のレポート（JSON のデータ）として持ち、カテ記録・CAG・PCI などの各画面はその一部を表示・編集する。保存はレポート単位。'),
        ('パスで項目を扱う', '入力部品はデータの場所（例 report.pci.lesions.0.target）を指定するだけで、値の読み書き・変更の検知・黄色表示・入力不可が働く。'),
        ('共有項目は 1 か所', '複数の画面に出る項目は保存場所を 1 つにし、編集できるのは主画面だけ。他の画面は参照表示とリンク。'),
        ('臨床ルールは関数', 'JCS 区分・ACC/AHA タイプ・J-CTO・病変成否・手技時間などの計算は 1 か所の関数にまとめ、画面・確認・帳票で同じ結果を使う。'),
        ('保存先を切り替え', '同じ画面で、ブラウザ内（Local Storage）とサーバー（MongoDB・PostgreSQL）を切り替えられる。'),
        ('サーバーでも検査', 'ログイン・権限・確定ロック・同時更新の検知・登録履歴の保護は、画面だけでなくサーバーでも検査する。'),
    ]
    return ('<h1>1. 心カテレポートシステムの概要と仕組み</h1>'
            '<p class="lead">心臓カテーテル検査（CAG・PCI など）の記録を、カテ記録から検査報告書・J-PCI レジストリ項目まで 1 つのレポートとして入力・保存・確定する Web システムです。'
            'カテ室の医師・秘書が検査の流れに沿って入力し、確定・照合した内容を検査報告書・カンファレンス・経過観察に使います。</p>' +
            table(['項目', '内容'], [((a, 'k'), b) for a, b in S.OVERVIEW], widths=['24mm', None]) +
            '<h2>1.1 システムの構成</h2>' + fig('ex_system', '利用者はブラウザで操作し、保存はサーバー（または試用時はブラウザ内）に行う。React 版と Thymeleaf 版は同じ画面・同じデータ形式', '105mm') +
            table(['版', '画面', 'サーバー・データベース', 'インストールなしで試す'], [((a, 'k'), b, c, (d, 'small')) for a, b, c, d in S.VERSIONS],
                  widths=['24mm', '42mm', None, '46mm']) +
            '<h2>1.2 仕組みの要点</h2>' + table(['仕組み', '内容'], [((a, 'k'), b) for a, b in mech], widths=['30mm', None]))


def p_funcs():
    return ('<h1>2. 主な機能</h1>'
            '<p class="lead">13 画面・約 1,000 項目。検査の流れに沿った画面と、計算・判定・転記の自動化が中心です。</p>' +
            table(['機能', '内容'], [((a, 'k'), b) for a, b in S.FUNCS], widths=['28mm', None]) +
            two_shots('01_list.png', '一覧（絞込・照合・状態）', '16_pci_lesion_morphology.png', 'PCI 病変形態（病変 1〜5 列、ACC/AHA の提案）'))


def p_model():
    rows = [
        ('患者', '1 人 1 件。ID・氏名・生年月日・アレルギー・感染症・既往歴', '患者 1 人に複数のレポート'),
        ('レポート', '1 検査 1 件。ヘッダ（施行日・Cine No など）、状態（入力中／確定）、照合、登録履歴、画面ごとのセクション', '保存・確定はレポート単位'),
        ('繰り返し項目', '側副血行 1〜5、グラフト 1〜4、ガイディング 1〜5・マイクロ 1〜4・GW 1〜5、PCI 病変 1〜5、Pressure Wire 1〜5（＝IVUS Lesion）、MACE 5、画像', '数は可変で最大数まで'),
        ('マスタ', '医師・施設・デバイス', '入力の候補'),
        ('保存の形', 'MongoDB：レポート 1 件 = 1 ドキュメント。PostgreSQL：ヘッダは列、画面ごとの項目は JSONB、画像は bytea、監査ログはトリガーで保護', '同じ JSON 形式'),
    ]
    links = [('同一', 'PCI の病変 i は PCI の全タブで同じデータ／病変名は Pressure Wire と IVUS で共有'),
             ('同じ番号', 'Pressure Wire の病変 N と IVUS の Lesion N（数・追加・削除が連動）'),
             ('名前の一致', 'Target の候補＝CAG セグメント、QCA 取得は Target と病変名で探す'),
             ('複写・集計', '前回 PCI 病変を Restudy へ取込、集計・帳票は Target のある病変を対象')]
    return ('<h1>3. データモデル</h1>'
            '<p class="lead">中心は「患者」と「レポート（1 検査）」です。レポートの中に画面ごとのセクションがあり、病変などの繰り返し項目は配列で持ちます。</p>' +
            fig('ex_model', '患者・レポート・画面ごとのセクション（青破線はデータの連携）', '105mm') +
            table(['データ', '内容', '補足'], [((a, 'k'), b, (c, 'small')) for a, b, c in rows], widths=['26mm', None, '40mm']) +
            '<h2>3.1 病変（Target）を軸にした連携</h2>'
            '<p>病変を表すデータは画面ごとに別の配列にあり、共通の病変 ID はありません。次の 4 種類でつながっています（詳しくは「画面間の共通データ」9 章・ER 図）。</p>' +
            table(['種類', '例'], [((a, 'k'), b) for a, b in links], widths=['26mm', None]) +
            fig('lesion_links', '病変（Target）を軸にしたデータ連携', '80mm'))


def p_features():
    return ('<h1>4. アプリの特徴</h1>' +
            table(['特徴', '内容'], [((a, 'k'), b) for a, b in S.FEATURES], widths=['34mm', None]) +
            two_shots('42_edit_save_button_red.png', '変更があると保存ボタンが赤く点滅', '46_dialog_confirm_check.png', '確定前の確認（未入力・自動判定との食い違い）'))


def p_flow():
    steps = [
        ('① ログイン', '全員', 'ログイン画面', '役割（医師・秘書・管理者・閲覧）で使える操作が決まる'),
        ('② 新規作成', '医師・秘書', '一覧 → 新規作成', '既存患者を検索して選ぶ／新規患者を登録。主治医・紹介元は患者情報から'),
        ('③ カテ記録', '医師・秘書', 'カテ記録', '検査情報・術者・シース・造影剤、手技の開始・終了時刻（手技時間は自動）、検査値（基準外はピンク）、既往歴・合併症。前回からコピー'),
        ('④ CAG/LVG', '医師', 'CAG/LVG', 'セグメントごとの狭窄度（JCS 区分を自動表示）、病変枝数の算出、側副血行・グラフト、LVG（EF 自動計算）'),
        ('⑤ PCI', '医師', 'PCI の各タブ', '病変（Target）ごとに形態（ACC/AHA の提案）・Device・CTO（J-CTO）・合併症・成否（自動判定）。J-PCI 項目・出血リスク・AMI の時間'),
        ('⑥ Pressure/IVUS・画像', '医師', 'Pressure/IVUS・画像', 'FFR などの指標（異常値はピンク）、IVUS の計算、QCA を PCI へ取得。画像の登録'),
        ('⑦ 保存・確認', '医師・秘書', '全画面', '保存（Ctrl+S）。確定前の確認で、必須項目の未入力と自動判定との食い違いを警告'),
        ('⑧ 確定・照合', '医師・管理者', 'サイドメニュー', '確定すると編集できなくなる（確定解除は権限が必要）。照合で内容の確認済みを記録'),
        ('⑨ 報告・共有', '医師', '検査報告書・カンファレンス', 'A4 の検査報告書を印刷。カンファレンスで病歴・所見・方針をまとめる'),
        ('⑩ 経過観察', '医師・秘書', 'MACE・Restudy・集計', 'MACE（イベント）の記録、再検査で前回 PCI 病変を取込んで再狭窄を評価、集計で成績を確認'),
    ]
    return ('<h1>5. カテレポートのワークフロー（簡単な流れ）</h1>'
            '<p class="lead">検査の流れに合わせて、左のメニューを上から順に入力していきます。途中で保存でき、確定するまで何度でも直せます。</p>' +
            fig('ex_flow', '1 件の検査の記録から報告・経過観察まで（上の段の右端から下の段の左端へ続く）', '70mm') +
            table(['手順', '主な担当', '画面', '内容・自動化'], [((a, 'k'), b, (c, 'small'), d) for a, b, c, d in steps], widths=['30mm', '22mm', '30mm', None]) +
            two_shots('06_cath_labs_risk.png', '③ カテ記録', '47_report_print.png', '⑨ 検査報告書'))


def p_good():
    pri = {k: f'<span class="pri {k}">{k}</span>' for k in ('高', '中', '低')}
    rows = [((e(a), 'k'), e(b), (pri[c], 'c'), (e(d), 'small')) for a, b, c, d in S.IMPROVE]
    return ('<h1>6. 良いところ</h1>' +
            table(['良いところ', '内容'], [((a, 'k'), b) for a, b in S.GOOD], widths=['34mm', None]) +
            '<h1 style="page-break-before:always">7. まだ改善・進化できること</h1>'
            '<h2>7.1 改善すること（優先度順）</h2>' +
            table(['区分', '内容', '優先度', '状況'], rows, widths=['22mm', None, '14mm', '34mm'], raw=True) +
            '<h2>7.2 進化の方向</h2>' +
            table(['方向', '内容'], [((a, 'k'), b) for a, b in S.EVOLVE], widths=['34mm', None]))


PARTS = [
    ('ov', 1, '1. 概要と仕組み', p_overview),
    ('fn', 1, '2. 主な機能', p_funcs),
    ('md', 1, '3. データモデル', p_model),
    ('ft', 1, '4. アプリの特徴', p_features),
    ('wf', 1, '5. ワークフロー', p_flow),
    ('gd', 1, '6. 良いところ／7. 改善・進化できること', p_good),
    ('rl', 1, '8. 関連資料', lambda: S.p_related().replace('7. 関連資料', '8. 関連資料')),
]

if __name__ == '__main__':
    make_figs()
    build_doc('心カテレポートシステム 説明資料', '仕組み・主な機能・データモデル・特徴・ワークフロー・良いところと改善',
              '心カテーテルレポート（React 版・Thymeleaf 版）', RELATED, PARTS, G.ROOT / 'docs/design/system_explanation.pdf')
