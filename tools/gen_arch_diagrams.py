#!/usr/bin/env python3
"""システム構成図・データフロー図・画面間データ連携図・シーケンス図を生成
出力: docs/architecture/*.svg / *.png / architecture_a3.pdf
usage: python3 tools/gen_arch_diagrams.py   （Graphviz・mermaid-cli(mmdc)・Chrome を使用）
"""
import json, pathlib, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/architecture'
OUT.mkdir(parents=True, exist_ok=True)
FONT = 'Noto Sans CJK JP'
FONT_FILE = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FONT_BOLD = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'

HEAD = f'''  graph [fontname="{FONT}", fontsize=12, pad=0.3, nodesep=0.35, ranksep=0.6, bgcolor="white", compound=true, newrank=true];
  node [fontname="{FONT}", fontsize=11, shape=box, style="rounded,filled", fillcolor="white", color="#7f939c", penwidth=1.2, margin="0.15,0.07"];
  edge [fontname="{FONT}", fontsize=10, color="#5d7b86", fontcolor="#33515c", penwidth=1.3, arrowsize=0.8];
'''

# =====================================================================
# 1. システム構成図
# =====================================================================
ARCH = 'digraph G {\n' + HEAD + '''  rankdir=TB; ranksep=0.55; nodesep=0.45;
  label=<<B>心カテーテルレポート　システム構成図</B><BR/><FONT POINT-SIZE="10">保存先は画面右上で Local Storage（既定）／Remote DB を切替。Node 版と Spring Boot 版は同一 REST API のため入替可能。</FONT>>; labelloc=t; fontsize=20;

  user [label="利用者\\n医師・技師・秘書", shape=ellipse, fillcolor="#fff7d6", color="#c9a227"];

  subgraph cluster_browser { label=<<B>クライアント（Web ブラウザ）</B>>; style="rounded,filled"; fillcolor="#eef6ee"; color="#6aa676";
    subgraph cluster_spa { label=<<B>React 18 + TypeScript SPA</B>（frontend/）>; style="rounded,filled"; fillcolor="#f7fbf7"; color="#9fc4a6";
      ui [label=<<B>画面コンポーネント</B><BR/><FONT POINT-SIZE="9">一覧／患者情報入力／カテ記録／CAG・LVG／PCI（10タブ）<BR/>Pressure・IVUS／PCPS／カンファレンス／MACE<BR/>画像／Restudy／集計</FONT>>, fillcolor="#e3f2e5"];
      layout [label=<<B>共通レイアウト</B><BR/><FONT POINT-SIZE="9">トップバー・サイドメニュー<BR/>患者属性ヘッダ・カテ履歴・ダイアログ</FONT>>];
      form [label=<<B>フォーム基盤</B>（form/）<BR/><FONT POINT-SIZE="9">FormContext・入力部品<BR/>パス指定バインド・変更判定・黄色表示<BR/>主画面判定（model/ownership.ts）</FONT>>];
      state [label=<<B>アプリ状態</B>（state/AppContext）<BR/><FONT POINT-SIZE="9">draft / original・isDirty<BR/>遷移ガード・保存・確定ロック</FONT>>, fillcolor="#e6f0fa"];
      model [label=<<B>データモデル</B>（types/・model/）<BR/><FONT POINT-SIZE="9">型定義・既定値・正規化(mergeDefaults)<BR/>計算(utils/calc)：BSA・EF・HBR・CREDO・D2B</FONT>>];
      adapter [label=<<B>StorageAdapter</B>（storage/）>, shape=component, fillcolor="#fdf1e2", color="#d8a25e"];
      lsa [label="LocalStorageAdapter", fillcolor="#fdf1e2", color="#d8a25e"];
      rsa [label="RemoteStorageAdapter\\n(fetch / JSON)", fillcolor="#fdf1e2", color="#d8a25e"];
    }
    ls [label=<<B>Local Storage</B><BR/><FONT POINT-SIZE="9">cath.patients / cath.reports<BR/>cath.masters（約5MB）</FONT>>, shape=cylinder, fillcolor="#ffffff", color="#d8a25e"];
  }

  subgraph cluster_server { label=<<B>アプリケーションサーバー</B>（どちらか一方を起動・ポート 8080・/api）>; style="rounded,filled"; fillcolor="#eef2f6"; color="#7f939c";
    subgraph cluster_node { label=<<B>Node.js 版</B>（backend-node/）>; style="rounded,filled"; fillcolor="#f6f9fc"; color="#b8c4c0";
      exp [label=<<B>Express</B><BR/><FONT POINT-SIZE="9">routes/api.ts<BR/>入力検証・重複/参照チェック</FONT>>];
      ndb [label=<<B>MongoDB Driver</B><BR/><FONT POINT-SIZE="9">db.ts（索引作成・seed）</FONT>>];
    }
    subgraph cluster_spring { label=<<B>Spring Boot 3 版</B>（backend-spring/）>; style="rounded,filled"; fillcolor="#f6f9fc"; color="#b8c4c0";
      ctl [label=<<B>@RestController</B><BR/><FONT POINT-SIZE="9">Patient / Report / Misc<BR/>Bean Validation・例外ハンドラ</FONT>>];
      svc [label=<<B>Service</B><BR/><FONT POINT-SIZE="9">ReportService（一覧射影）<BR/>SampleDataService（seed）</FONT>>];
      repo [label=<<B>Spring Data MongoDB</B><BR/><FONT POINT-SIZE="9">MongoRepository・MongoTemplate</FONT>>];
    }
  }

  mongo [label=<<B>MongoDB 7</B><BR/><FONT POINT-SIZE="9">patients<BR/>cath_reports（1検査＝1ドキュメント）<BR/>masters</FONT>>, shape=cylinder, fillcolor="#e8f4ea", color="#4c9a5a", penwidth=1.6];
  sample [label=<<B>サンプルデータ</B><BR/><FONT POINT-SIZE="9">sample-data/*.json<BR/>患者8・レポート9・画像38</FONT>>, shape=note, fillcolor="#fffde7"];

  subgraph cluster_ext { label=<<B>外部システム（ボタンのみ・未接続）</B>>; style="rounded,dashed"; color="#b0b0b0"; fontcolor="#777";
    node [color="#b0b0b0", fontcolor="#777", style="rounded,dashed"];
    ext1 [label="電子カルテ・病歴総括\\nG-NAVI・WEB・予定表"];
    ext2 [label="検査システム（採血取得）\\nポリグラフ（数値取得）"];
    ext3 [label="J-PCI 登録フォーム"];
  }

  user -> ui [label="操作・入力"];
  {rank=same; ui; layout;}
  {rank=same; form; model;}
  {rank=same; lsa; rsa;}
  {rank=same; exp; ctl;}
  {rank=same; ndb; svc;}
  ui -> layout [dir=none, style=dotted];
  ui -> form; form -> state; state -> model [dir=both, style=dashed, label="正規化・計算"];
  state -> adapter [label="読込・保存"];
  adapter -> lsa [arrowhead=empty, style=dashed]; adapter -> rsa [arrowhead=empty, style=dashed];
  lsa -> ls [label="JSON"];
  rsa -> exp [label="HTTP/JSON\\n/api/*", color="#c9772e", fontcolor="#c9772e", penwidth=2];
  rsa -> ctl [label="HTTP/JSON\\n/api/*", color="#c9772e", fontcolor="#c9772e", penwidth=2];
  exp -> ndb; ndb -> mongo;
  ctl -> svc -> repo -> mongo;
  sample -> ls [style=dashed, label="初回起動時投入"];
  sample -> ndb [style=dashed, label="起動時(空のとき)"];
  sample -> svc [style=dashed];
  user -> ext1 [style=invis]; ext1 -> ext2 [style=invis]; ext2 -> ext3 [style=invis];
  ui -> ext1 [style=dashed, color="#b0b0b0", constraint=false, label="（将来連携）", fontcolor="#999"];
}
'''

# =====================================================================
# 2. データフロー図（DFD）
# =====================================================================
P = 'shape=circle, fixedsize=true, width=1.45, fillcolor="#e6f0fa", color="#5b84b1", fontsize=10'
DS = 'shape=cds, fillcolor="#fdf1e2", color="#d8a25e", fontsize=10, margin="0.2,0.05"'
EXT = 'shape=box, style="filled", fillcolor="#fff7d6", color="#c9a227"'
DFD = 'digraph G {\n' + HEAD + f'''  rankdir=LR; ranksep=0.8;
  label=<<B>心カテーテルレポート　データフロー図（DFD レベル1）</B><BR/><FONT POINT-SIZE="10">○ プロセス　▭ 外部実体　▱ データストア。保存は「患者（変更時のみ）→ レポート」の順で一括置換。</FONT>>; labelloc=t; fontsize=20;

  u1 [label="利用者\\n（医師・技師）", {EXT}];
  u2 [label="利用者\\n（秘書・管理者）", {EXT}];
  prn [label="印刷物\\n検査報告書・時間経過シート\\nJ-PCI・連携パス", {EXT}];

  p1 [label="1.0\\n一覧検索\\n絞込", {P}];
  p2 [label="2.0\\nレポート\\n読込・正規化", {P}];
  p3 [label="3.0\\n入力・編集\\n(draft)", {P}];
  p4 [label="4.0\\n自動計算\\n画面間参照", {P}];
  p5 [label="5.0\\n変更判定\\n遷移ガード", {P}];
  p6 [label="6.0\\n検証・保存\\n登録履歴付与", {P}];
  p7 [label="7.0\\n集計\\n印刷", {P}];
  p8 [label="8.0\\nマスタ管理\\nサンプル投入", {P}];

  d1 [label="D1 patients（患者）", {DS}];
  d2 [label="D2 cath_reports（カテレポート）", {DS}];
  d3 [label="D3 masters（術者・病院・デバイス）", {DS}];
  d4 [label="D4 sample-data（サンプル JSON）", {DS}];

  u1 -> p1 [label="検索条件\\n(施行日・ID・氏名・状態)"];
  d2 -> p1 [label="レポート一覧\\n(画像本体除く)"];
  d1 -> p1 [label="患者属性"];
  p1 -> u1 [label="一覧・該当件数"];
  u1 -> p2 [label="レコード選択\\n新規作成"];
  d2 -> p2 [label="レポート全体"]; d1 -> p2 [label="患者"];
  p2 -> p3 [label="draft / original\\n(全項目補完済)"];
  u1 -> p3 [label="入力値・画像"];
  d3 -> p3 [label="入力候補"];
  p3 -> p4 [label="入力値"];
  p4 -> p3 [label="算出値(BSA・EF・D2B\\nHBR・CREDO・IVUS)\\n参照値・コピー値"];
  p3 -> p5 [label="draft"];
  p5 -> u1 [label="保存ボタン赤\\n放棄/キャンセル確認\\n変更項目の黄色表示"];
  u1 -> p6 [label="保存(Ctrl+S)"];
  p5 -> p6 [label="変更あり"];
  p6 -> d1 [label="患者(変更時)"];
  p6 -> d2 [label="レポート\\n+history"];
  p6 -> u1 [label="結果通知\\n必須エラー"];
  d2 -> p7 [label="絞込済レポート"];
  p7 -> u1 [label="件数・成功率・D2B"];
  p7 -> prn [label="帳票"];
  u2 -> p8 [label="マスタ編集\\n保存先切替"];
  p8 -> d3 [label="マスタ"];
  d4 -> p8 [label="サンプル"];
  p8 -> d1 [label="初期データ", style=dashed]; p8 -> d2 [label="初期データ", style=dashed];
  {{rank=same; d1; d2; d3;}}
}}
'''

# =====================================================================
# 3. 画面間データ連携図
# =====================================================================
S = 'shape=box, style="rounded,filled", fillcolor="#e3f2e5", color="#6aa676", fontsize=12, penwidth=1.6, margin="0.25,0.12"'
LINK = 'digraph G {\n' + HEAD + f'''  rankdir=LR; ranksep=1.3; nodesep=0.5;
  label=<<B>心カテーテルレポート　画面間データ連携図</B><BR/><FONT POINT-SIZE="10">青実線：参照（主画面のみ編集可・他画面は参照表示）　橙破線：ボタン操作でコピー/取込　紫点線：自動計算して表示</FONT>>; labelloc=t; fontsize=20;
  edge [fontsize=9];

  pat [label="患者情報入力", {S}, fillcolor="#f4efe0", color="#b9a76f"];
  hdr [label="全画面ヘッダ\\n（患者属性・カテ履歴）", {S}, fillcolor="#f4efe0", color="#b9a76f"];
  cath [label="カテ記録", {S}];
  cag [label="CAG / LVG", {S}, fillcolor="#e6f0fa", color="#5b84b1"];
  pci [label="PCI\\n基本・病変形態・Device・Bif/CTO\\nComplication・J-PCI・リスク・AMI", {S}, fillcolor="#fdf1e2", color="#d8a25e"];
  pw [label="Pressure / IVUS", {S}, fillcolor="#f3e8f7", color="#9b6bb3"];
  conf [label="カンファレンス", {S}, fillcolor="#e8f4f3", color="#5a9a96"];
  img [label="画像", {S}, fillcolor="#eef0f2", color="#7f939c"];
  rs [label="Restudy", {S}, fillcolor="#eef0f2", color="#7f939c"];
  mace [label="MACE", {S}, fillcolor="#fbeaea", color="#c97b76"];
  list [label="一覧・集計", {S}, fillcolor="#eef0f2", color="#7f939c"];

  edge [color="#2f6fb0", fontcolor="#2f6fb0", penwidth=1.6];
  pat -> hdr [label="ID・氏名・性別・生年月日"];
  cath -> hdr [label="施行日・Cine No"];
  pat -> conf [label="感染症・既往歴・病歴総括"];
  cath -> pci [label="透視時間・造影剤\\n危険因子(DM/HT/HD/HL)・Hb・Cr"];
  cath -> conf [label="危険因子・血行動態・身長体重\\n予後・HBs/HCV"];
  cag -> pci [label="Syntax・Euro・Japan Score"];
  cag -> conf [label="LVEDV/LVESV/SV(I)・EF"];
  cath -> list [label="疾病・検査項目・術者\\n主治医・緊急・FollowUp"];
  pci -> img [label="Target（対象病変候補）"];

  edge [color="#d8842e", fontcolor="#c06a12", style=dashed];
  pw -> pci [label="QCA（Ref・%DS・MLD）\\n「取得」ボタン"];
  pci -> rs [label="前回PCI病変・Post%\\n「前回PCI病変を取込」"];
  cath -> cag [label="アプローチ・シース\\n「カテ記録のアプローチを反映」"];
  cag -> conf [label="CAGコメント\\n「CAGコメントをコピー」"];
  cag -> cath [label="過去のCAGComment\\n（同一患者の過去レポート）"];
  pat -> conf [label="病歴総括\\n「病歴総括からコピー」", constraint=false];
  cath -> mace [label="施行日 → PCI行った日付\\n「施行日を反映」"];

  edge [color="#7b4bb3", fontcolor="#6a3d9a", style=dotted, penwidth=1.8];
  cath -> cag [label="身長・体重(BSA)・HR\\n→ LVEDVI 等の算出"];
  pci -> list [label="AMI 時刻 → Door to balloon\\n病変成功率"];
  pci -> pci [label="AMI → D2B（基本・J-PCI表示）\\nDevice → 最終Balloon径・総Stent長"];
}}
'''

# =====================================================================
# 4. シーケンス図（mermaid）
# =====================================================================
SEQ = '''sequenceDiagram
    autonumber
    actor U as 利用者
    participant V as 画面（React）
    participant S as AppContext（draft/original）
    participant A as StorageAdapter
    participant B as REST API（Node / Spring）
    participant M as MongoDB
    Note over V,M: 【読込】一覧からレコードを開く
    U->>V: 一覧で行を選択
    V->>S: openReport(id)
    S->>S: guard()：未保存の変更があれば確認ダイアログ
    S->>A: getReport(id) / getPatient(patientRef)
    alt Remote DB
        A->>B: GET /api/reports/{id}, /api/patients/{id}
        B->>M: find(_id)
        M-->>B: document
        B-->>A: JSON
    else Local Storage
        A->>A: localStorage から取得
    end
    A-->>S: normalize（既定値で全項目補完）
    S-->>V: draft = original（変更なし）
    Note over U,S: 【編集】
    U->>V: 入力（例：カテ記録の Hb）
    V->>S: set("report.cathRecord.labs.cbc.Hb", 値)
    S-->>V: 再描画（J-PCI など参照画面にも反映）／保存ボタン赤
    Note over U,S: 【画面遷移】
    U->>V: 別画面へ移動
    V->>S: guard(goto)
    alt 変更あり
        S-->>U: 「変更が有ります。修正を放棄しますか？」
        U->>S: 放棄 → draft を original に戻して遷移
        U->>S: キャンセル → 遷移せず変更項目を黄色表示
    end
    Note over U,M: 【保存】
    U->>V: 保存（Ctrl+S）
    V->>S: save()
    S->>S: 必須チェック（患者ID・氏名・施行日）／登録履歴を追加
    opt 患者が変更された場合
        S->>A: savePatient
        A->>B: PUT /api/patients/{id}
        B->>M: replaceOne(upsert)
    end
    S->>A: saveReport
    A->>B: PUT /api/reports/{id}
    B->>M: replaceOne(upsert)
    M-->>B: OK
    B-->>A: 保存済み JSON
    A-->>S: original = draft
    S-->>V: 一覧更新・「保存しました」
'''


def dot_render(name, dot):
    p = OUT / f'{name}.dot'
    p.write_text(dot, encoding='utf-8')
    subprocess.run(['dot', '-Tsvg', '-o', str(OUT / f'{name}.svg'), str(p)], check=True, stderr=subprocess.DEVNULL)
    svg = OUT / f'{name}.svg'
    svg.write_text(svg.read_text(encoding='utf-8').replace(f'font-family="{FONT}"', f'font-family="{FONT}, Meiryo, Yu Gothic, sans-serif"'), encoding='utf-8')
    subprocess.run(['dot', '-Tpng', '-Gdpi=170', '-o', str(OUT / f'{name}.png'), str(p)], check=True, stderr=subprocess.DEVNULL)


def mmd_render(name, src):
    mmd = OUT / f'{name}.mmd'
    mmd.write_text(src, encoding='utf-8')
    pp = pathlib.Path(tempfile.mktemp(suffix='.json'))
    pp.write_text(json.dumps({'executablePath': '/usr/bin/google-chrome', 'args': ['--no-sandbox']}))
    cfg = pathlib.Path(tempfile.mktemp(suffix='.json'))
    cfg.write_text(json.dumps({'theme': 'neutral', 'themeVariables': {'fontFamily': 'Noto Sans CJK JP, Meiryo, sans-serif', 'fontSize': '15px'},
                               'sequence': {'mirrorActors': False, 'messageFontSize': 14, 'noteFontSize': 13, 'actorFontSize': 15}}))
    for ext, extra in (('svg', []), ('png', ['-s', '2'])):
        subprocess.run(['mmdc', '-i', str(mmd), '-o', str(OUT / f'{name}.{ext}'), '-p', str(pp), '-c', str(cfg), '-b', 'white', *extra],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


dot_render('01_system_architecture', ARCH)
dot_render('02_data_flow', DFD)
dot_render('03_screen_data_links', LINK)
mmd_render('04_sequence_load_edit_save', SEQ)

# ---- A3 PDF（各図を1ページ、向き自動）
DPI = 200
A3 = (int(420 / 25.4 * DPI), int(297 / 25.4 * DPI))
M = int(10 / 25.4 * DPI)
TITLES = {'01_system_architecture': 'システム構成図', '02_data_flow': 'データフロー図', '03_screen_data_links': '画面間データ連携図',
          '04_sequence_load_edit_save': '処理シーケンス図（読込・編集・画面遷移・保存）'}
pages = []
for i, (stem, title) in enumerate(TITLES.items(), 1):
    img = Image.open(OUT / f'{stem}.png').convert('RGB')
    best = None
    for size in (A3, A3[::-1]):
        sc = min((size[0] - 2 * M) / img.width, (size[1] - 2 * M - 110) / img.height, 1.6)
        if not best or sc > best[0]:
            best = (sc, size)
    sc, size = best
    pg = Image.new('RGB', size, 'white')
    im = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
    pg.paste(im, ((size[0] - im.width) // 2, M + 90 + (size[1] - 2 * M - 110 - im.height) // 2))
    d = ImageDraw.Draw(pg)
    d.text((M, M), f'心カテーテルレポート　{title}', font=ImageFont.truetype(FONT_BOLD, 44), fill='#2c3e45')
    d.line((M, M + 70, size[0] - M, M + 70), fill='#b8c4c0', width=3)
    t = f'{i} / {len(TITLES)}'
    f = ImageFont.truetype(FONT_FILE, 24)
    d.text((size[0] - M - d.textlength(t, font=f), size[1] - M - 30), t, font=f, fill='#8a9894')
    pg.save(OUT / f'{stem}_a3.png', dpi=(DPI, DPI))
    pages.append(pg)
pages[0].save(OUT / 'architecture_a3.pdf', save_all=True, append_images=pages[1:], resolution=DPI)
for p in sorted(OUT.iterdir()):
    print(p.name, p.stat().st_size // 1024, 'KB')
