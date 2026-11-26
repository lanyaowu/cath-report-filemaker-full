#!/usr/bin/env python3
"""React 版 設計資料の図（Graphviz / Mermaid）を生成する。出力: docs/design/img/*.svg"""
import json, pathlib, subprocess, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/design/img'
FONT = 'Noto Sans CJK JP'

HEAD = f'''  graph [fontname="{FONT}", fontsize=12, pad=0.25, nodesep=0.3, ranksep=0.5, bgcolor="white", compound=true, newrank=true];
  node [fontname="{FONT}", fontsize=11, shape=box, style="rounded,filled", fillcolor="white", color="#7f939c", penwidth=1.2, margin="0.14,0.06"];
  edge [fontname="{FONT}", fontsize=9.5, color="#5d7b86", fontcolor="#33515c", penwidth=1.2, arrowsize=0.75];
'''

# =====================================================================
# 1.1 システム構成図
# =====================================================================
SYSTEM = 'digraph G {\n' + HEAD + '''  rankdir=TB; ranksep=0.55; nodesep=0.45;
  user [label="利用者\\n医師・技師・秘書", shape=ellipse, fillcolor="#fff7d6", color="#c9a227"];

  subgraph cluster_browser { label=<<B>ブラウザ（Chrome / Edge）</B>>; style="rounded,filled"; fillcolor="#f2f8f3"; color="#6aa676"; fontsize=13;
    subgraph cluster_spa { label=<<B>React SPA</B>（React 18 + TypeScript、Vite でビルド）>; style="rounded,filled"; fillcolor="#e3f2e5"; color="#6aa676";
      ui [label=<<B>画面コンポーネント</B><BR/><FONT POINT-SIZE="9">TopBar・SideNav・13画面・ダイアログ</FONT>>];
      form [label=<<B>フォームバインディング</B><BR/><FONT POINT-SIZE="9">FormContext・Scope・fields.tsx<BR/>（パスで値を読み書き）</FONT>>];
      state [label=<<B>アプリ状態</B>（AppContext）<BR/><FONT POINT-SIZE="9">draft / original・isDirty・guard<BR/>save・openReport・newReport</FONT>>, fillcolor="#e6f0fa", color="#5b84b1"];
      domain [label=<<B>モデル・ロジック</B><BR/><FONT POINT-SIZE="9">types/model・model/defaults<BR/>model/ownership・utils/calc</FONT>>];
      adp [label=<<B>StorageAdapter</B>（storage/）<BR/><FONT POINT-SIZE="9">保存先を設定で切替（既定：LocalStorage）</FONT>>, fillcolor="#fdf1e2", color="#d8a25e"];
      ls [label=<<B>LocalStorageAdapter</B>>, fillcolor="#fdf1e2", color="#d8a25e"];
      rs [label=<<B>RemoteStorageAdapter</B><BR/><FONT POINT-SIZE="9">fetch（REST /api）</FONT>>, fillcolor="#fdf1e2", color="#d8a25e"];
    }
    lsdb [label=<<B>localStorage</B><BR/><FONT POINT-SIZE="9">cath.patients / cath.reports<BR/>cath.masters / cath.storageSettings</FONT>>, shape=cylinder, fillcolor="#ffffff", color="#d8a25e"];
  }

  subgraph cluster_be { label=<<B>バックエンド（Remote DB 選択時。いずれか1つ・同じ REST API）</B>>; style="rounded,dashed"; color="#5b84b1"; fontcolor="#2f6fb0"; fontsize=13;
    node1 [label=<<B>Node.js 版</B>（backend-node）<BR/><FONT POINT-SIZE="9">Express + mongodb ドライバ<BR/>TypeScript・ポート 3001</FONT>>, fillcolor="#eef2f6"];
    spr1 [label=<<B>Spring Boot 版</B>（backend-spring）<BR/><FONT POINT-SIZE="9">Spring Data MongoDB<BR/>Java 17・ポート 8080</FONT>>, fillcolor="#eef2f6"];
    spr2 [label=<<B>Spring Boot + PostgreSQL 版</B><BR/>（backend-spring-pg）<BR/><FONT POINT-SIZE="9">Spring Data JPA・Flyway<BR/>列＋JSONB・画像 bytea</FONT>>, fillcolor="#eef2f6"];
  }
  mongo [label=<<B>MongoDB</B><BR/><FONT POINT-SIZE="9">patients・cath_reports・masters</FONT>>, shape=cylinder, fillcolor="#e8f4ea", color="#4c9a5a"];
  pg [label=<<B>PostgreSQL</B><BR/><FONT POINT-SIZE="9">patients・cath_reports ほか 8表</FONT>>, shape=cylinder, fillcolor="#e8f4ea", color="#4c9a5a"];
  sample [label=<<B>サンプルデータ</B><BR/><FONT POINT-SIZE="9">sample-data/*.json<BR/>患者8・レポート9・画像38</FONT>>, shape=note, fillcolor="#fffde7"];

  user -> ui [label="操作"];
  ui -> form [label="入力欄"]; form -> state [label="set(パス, 値)"]; ui -> state [label="画面遷移・保存"];
  state -> domain [dir=none, style=dotted]; form -> domain [dir=none, style=dotted, label="主画面判定"];
  state -> adp [label="読込・保存"];
  adp -> ls; adp -> rs;
  ls -> lsdb;
  rs -> node1 [label="HTTP JSON", color="#2f6fb0"]; rs -> spr1 [color="#2f6fb0"]; rs -> spr2 [color="#2f6fb0"];
  node1 -> mongo; spr1 -> mongo; spr2 -> pg;
  sample -> node1 [style=dashed, label="DB が空なら投入"]; sample -> spr1 [style=dashed]; sample -> spr2 [style=dashed];
  sample -> lsdb [style=dashed, label="初回・サンプル投入", constraint=false];
  {rank=same; ui; form;} {rank=same; ls; rs;} {rank=same; node1; spr1; spr2; sample;} {rank=same; mongo; pg;}
}
'''

# =====================================================================
# 1.2 コンポーネント構成図
# =====================================================================
C = 'fillcolor="#e3f2e5", color="#6aa676"'
S = 'fillcolor="#e6f0fa", color="#5b84b1"'
D = 'fillcolor="#fdf1e2", color="#d8a25e"'
G = 'fillcolor="#f3f3f3", color="#9aa5a9", fontsize=10'
COMP = 'digraph G {\n' + HEAD + f'''  rankdir=LR; ranksep=0.45; nodesep=0.12;
  node [fontsize=10.5];
  main [label="main.tsx", {G}];
  app [label=<<B>App</B><BR/><FONT POINT-SIZE="9">AppProvider でラップ</FONT>>, {S}];
  prov [label=<<B>AppProvider</B><BR/><FONT POINT-SIZE="9">状態・操作（AppContext）</FONT>>, {S}];
  mainc [label=<<B>Main</B><BR/><FONT POINT-SIZE="9">画面の切替・Ctrl+S<BR/>確認/通知ダイアログ</FONT>>, {S}];
  main -> app -> prov -> mainc;

  top [label="TopBar", {C}]; side [label="SideNav", {C}];
  dlgS [label="SettingsDialog\\n保存先の切替", {D}]; dlgN [label="NewReportDialog\\n患者選択", {D}]; dlgM [label="MasterDialog\\nマスタ編集", {D}];
  modal [label="Modal（確認）・Toast", {G}];
  mainc -> top; mainc -> side; mainc -> modal;
  top -> dlgS; top -> dlgN; top -> dlgM;

  list [label="ReportList\\n一覧", {C}]; stats [label="StatsScreen\\n集計", {C}];
  fp [label=<<B>FormProvider</B><BR/><FONT POINT-SIZE="9">draft を入力欄へ提供</FONT>>, {S}];
  mainc -> list; mainc -> stats; mainc -> fp;

  frame [label=<<B>ScreenFrame</B><BR/><FONT POINT-SIZE="9">ロック表示＋PatientHeader</FONT>>, {C}];
  ph [label="PatientHeader\\n患者属性・カテ履歴", {C}];
  frame -> ph;

  subgraph cluster_screens {{ label=<<B>入力画面（10）</B>>; style="rounded,dashed"; color="#9fb2bb";
    pat [label="PatientInfo\\n患者情報入力", {C}];
    cath [label="CathRecordScreen\\nカテ記録", {C}];
    cag [label="CagLvgScreen\\nCAG/LVG", {C}];
    rs [label="RestudyScreen", {C}];
    pci [label="PciScreen\\nPCI", {C}];
    pw [label="PressureIvusScreen", {C}];
    img [label="ImagesScreen\\n画像", {C}];
    pcps [label="PcpsScreen", {C}];
    conf [label="ConferenceScreen\\nカンファレンス", {C}];
    mace [label="MaceScreen", {C}];
  }}
  fp -> pat; fp -> cath; fp -> cag; fp -> rs; fp -> pci; fp -> pw; fp -> img; fp -> pcps; fp -> conf; fp -> mace;
  pat -> frame [style=dotted, arrowhead=none, label="全画面で使用", fontsize=8.5];

  cath -> exam [label=""]; exam [label="ExamInfoPanel\\n検査情報", {G}];
  cath -> sidep; sidep [label="SidePanels\\n主治医・術者／血行動態\\n予後／その他", {G}];
  cath -> labs; labs [label="LabsPanel\\n検査値・危険因子（4タブ）", {G}];
  cag -> catp; catp [label="CatheterPanel\\nアプローチ・カテーテル", {G}];
  cag -> cagt; cagt [label="CagTab\\nセグメント・側副血行・グラフト", {G}];
  cag -> lvgt; lvgt [label="LvgTab\\n左室造影・壁運動", {G}];
  cagt -> past; past [label="PastCopy\\n過去所見/コメントのコピー", {G}];
  pci -> basic; basic [label="BasicTab\\n基本・術前検査/投薬", {G}];
  pci -> lt; lt [label="LesionTabs\\n病変形態・Device\\nBif/CTO・Complication", {G}];
  lt -> lg; lg [label="LesionGrid\\n病変の表（1〜5列）", {G}];
  pci -> jp; jp [label="JpciTab\\nJ-PCI 登録項目", {G}];
  pci -> br; br [label="BleedingRiskTab\\n出血・血栓リスク", {G}];
  pci -> ami; ami [label="AmiTab\\nAMI 時刻・時間経過シート", {G}];
  pci -> st; st [label="SearchTab\\n検索用", {G}];
  pci -> ref; ref [label="ReferenceTab\\n参考資料（図）", {G}];
  pcps -> ami [style=dashed, label="TimelineSheet", fontsize=8.5];

  subgraph cluster_common {{ label=<<B>共通部品</B>>; style="rounded,filled"; fillcolor="#fafafa"; color="#c9d1d6";
    ui [label=<<B>common/ui.tsx</B><BR/><FONT POINT-SIZE="9">Panel・Tabs・Modal・Btn・Toast・Row・Col</FONT>>, {G}];
    fld [label=<<B>form/fields.tsx</B><BR/><FONT POINT-SIZE="9">TextF・NumF・DateF・TimeF・SelectF・TextAreaF<BR/>CheckF・RadioF・TripleF・DateTimeF・Calc・RefLink</FONT>>, {G}];
    fc [label=<<B>form/FormContext.tsx</B><BR/><FONT POINT-SIZE="9">Scope・useField・useVal・useResolve</FONT>>, {G}];
  }}
  fld -> fc [style=dashed];
}}
'''

# =====================================================================
# 3.1 データモデル全体構造
# =====================================================================
def ent(name, jp, rows, fill='#ffffff', head='#e3f2e5'):
    r = ''.join(f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="9.5">{a}</FONT></TD><TD ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#5c7078">{b}</FONT></TD></TR>' for a, b in rows)
    return (f'  {name} [shape=plaintext, label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#8aa898" BGCOLOR="{fill}">'
            f'<TR><TD BGCOLOR="{head}" COLSPAN="2"><B>{name}</B>  <FONT POINT-SIZE="9.5">{jp}</FONT></TD></TR>{r}</TABLE>>];\n')

MODEL = 'digraph G {\n' + HEAD + '''  rankdir=LR; ranksep=0.7; nodesep=0.18; splines=true;
  edge [arrowhead=none, arrowtail=diamond, dir=both, arrowsize=0.9];
''' + ent('Patient', '患者', [('id / patientId', 'アプリ内ID / 病院ID'), ('name・kana・sex・birthDate', '基本情報'), ('emergency・insurance', '連絡先・保険'), ('allergy・infection', 'アレルギー・感染症'), ('primaryDoctor・referral', '主治医・紹介元'), ('pastHistory…notes', '既往歴・メモ'), ('admissions[ ]', '病歴総括'), ('createdAt・updatedAt', '作成・更新日時')], head='#f4efe0') \
 + ent('Admission', '病歴総括（入退院）', [('admitDate・dischargeDate', '入院日・退院日'), ('doctor・diagnosis・summary', '担当医・診断・要約')], head='#f4efe0') \
 + ent('CathReport', 'カテレポート（1検査=1件）', [('id / patientRef', 'ID / 患者（→ Patient.id）'), ('status・verified', '入力中/確定・照合済'), ('header', '施行日・Cine No・PCI No 等'), ('cathRecord', 'カテ記録'), ('cagLvg', 'CAG/LVG'), ('pci', 'PCI'), ('pressureIvus', 'Pressure/IVUS'), ('pcps', 'PCPS'), ('conference', 'カンファレンス'), ('mace[ ]', 'MACE（5件）'), ('images[ ]', '画像'), ('restudy', 'Restudy'), ('history[ ]', '登録履歴')], fill='#ffffff', head='#dcebe2') \
 + ent('CathRecord', 'カテ記録', [('exam', '検査情報（目的・項目・シース・造影剤・透視）'), ('doctors', '主治医・術者×3・助手×3・紹介'), ('hemo', '血行動態（Triple ×8・値）'), ('labs', '検査値（入院時・血算・内分泌・退院時・血ガス・旧）'), ('risk', '危険因子（DM・HT・HL・喫煙…）'), ('body', '身長・体重・体温'), ('prognosis・other', '予後・その他'), ('pciSummary・comment', 'サマリー・コメント')]) \
 + ent('CagLvg', 'CAG / LVG', [('approach', 'アプローチ（動脈・静脈・シース）'), ('catheters', 'カテーテル（10枠）'), ('cag.segments', 'セグメント所見（AHA分類）'), ('cag.collaterals[ ]', '側副血行路'), ('cag.grafts[ ]', 'バイパスグラフト'), ('cag.lesions・syntax…', '病変枝・スコア'), ('lvg', '左室造影（値・壁運動・MR）')]) \
 + ent('Pci', 'PCI', [('basic', '基本（病変数・ガイディング・GW）'), ('lesions[5]', '病変（PciLesion）'), ('patientComp・patientTreat', '患者合併症・処置'), ('jpci', 'J-PCI 登録（背景・術前・術後・情報）'), ('risk', '出血（HBR）・血栓（CREDO）'), ('ami', 'AMI 時刻（発症〜最初のdevice）')]) \
 + ent('PciLesion', 'PCI 病変（1〜5）', [('target・targetSub', '病変キー（#番号）・血管'), ('type・deNovo', 'タイプ・de novo'), ('morph', '病変形態'), ('pre・post', 'QCA（Ref・%DS・MLD）'), ('device.items[10]', 'デバイス（DeviceItem）'), ('device.final', '最終Balloon・総Stent長・最大圧'), ('bif・cto', '分岐部・CTO'), ('comp', '合併症'), ('summary', '治療・前後%・TIMI')]) \
 + ent('DeviceItem', 'デバイス', [('category・name', 'カテゴリ・名称（マスタ）'), ('size・length・pressure', 'サイズ・長さ・圧')]) \
 + ent('PressureIvus', 'Pressure / IVUS', [('pressure[1..5]', 'Pressure Wire の病変（PressureCol）'), ('lesions[1..5]', 'IVUS 病変（IvusLesion。pressure と同じ番号）')]) \
 + ent('PressureCol', 'Pressure Wire 列', [('lesion', '病変名（IVUS と共有）'), ('phase・drug', 'Pre/Post・薬剤'), ('metrics', 'FFR・iFR・RFR・DFR・dPR…'), ('qca', 'QCA（Ref・%DS・MLD）')]) \
 + ent('IvusLesion', 'IVUS 病変', [('site', '旧：部位（病変名は pressure[N].lesion）'), ('pre・post', '指標×位置（病変・近位・遠位）'), ('fibrofatty…calcDegree', 'プラーク性状')]) \
 + ent('Pcps', 'PCPS', [('arrest…start', '時刻（DateTime ×7）'), ('firstEcg・operators・rosc', '初期波形・術者・ROSC'), ('detail', '送脱血・流量・離脱・転帰')]) \
 + ent('Conference', 'カンファレンス', [('wardDoctor・disease・nyha…', '基本'), ('prevPci[ ]', '前回PCI'), ('scinti・mdct・ucg・treadmill', '各種検査'), ('clinical・history', '臨床診断・既往/経過'), ('dischargeRx[ ]', '退院時処方（MedRow）')]) \
 + ent('MaceEntry', 'MACE（×5）', [('mace・pciDate・lastVisit', 'MACE・PCI日・最終受診'), ('death・acs・stroke・hf', 'イベント（有無・日付）'), ('bleeding・revasc・other', 'イベント（部位等）')]) \
 + ent('ImageItem', '画像', [('category・takenAt・view・lesion', '種別・撮影日・方向・病変'), ('title・description', 'タイトル・所見'), ('dataUrl・keyImage', '画像データ・キー画像')]) \
 + ent('Restudy', 'Restudy', [('date・interval', '施行日・間隔'), ('lesions[5]', '再評価（前回 PCI から取込）')]) \
 + ent('ReportHistory', '登録履歴', [('at・by・action', '日時・登録者・操作')]) \
 + ent('Masters', 'マスタ', [('doctors[ ]', '術者・医師'), ('hospitals[ ]', '紹介病院'), ('devices[ ]', 'デバイス（カテゴリ・名称）')], head='#ececec') \
 + '''
  Patient -> Admission [label="1 : N"];
  Patient -> CathReport [arrowhead=crow, arrowtail=teetee, style=dashed, color="#c0504d", fontcolor="#c0504d", label="1 : N\\npatientRef"];
  CathReport -> CathRecord; CathReport -> CagLvg; CathReport -> Pci; CathReport -> PressureIvus; CathReport -> Pcps;
  CathReport -> Conference; CathReport -> MaceEntry [label="1 : 5"]; CathReport -> ImageItem [label="1 : N"]; CathReport -> Restudy;
  CathReport -> ReportHistory [label="1 : N"];
  Pci -> PciLesion [label="1 : 1〜5"]; PciLesion -> DeviceItem [label="1 : 10"];
  PressureIvus -> PressureCol [label="1 : 1〜5"]; PressureIvus -> IvusLesion [label="1 : 1〜5"];
  /* データの連携（青破線）：外部キーではなく、同じ番号・名前の一致・複写でつながる */
  edge [dir=forward, arrowhead=vee, arrowtail=none, style=dashed, color="#2b6cb0", fontcolor="#2b6cb0", fontsize=9, constraint=false];
  PressureCol -> IvusLesion [label="同じ番号 N\n病変名を共有", dir=both, arrowtail=vee];
  PressureCol -> PciLesion [label="QCA 取得\n（lesion と target の一致）"];
  CagLvg -> PciLesion [label="target の候補\n（CAG セグメント）"];
  PciLesion -> ImageItem [label="lesion の候補"];
  PciLesion -> Restudy [label="次回レポートへ取込\n（target・術後%）"];
  Masters -> DeviceItem [arrowhead=none, style=dotted, label="名称の候補", color="#9aa5a9"];
  {rank=same; Patient; Masters;}
}
'''

# =====================================================================
# 5.1 論理ビュー（レイヤー）
# =====================================================================
L = 'shape=box, style="rounded,filled", fillcolor="white", color="#7f939c", fontsize=10.5'
LOGIC = 'digraph G {\n' + HEAD + f'''  rankdir=TB; ranksep=0.42; nodesep=0.22;
  subgraph cluster_p {{ label=<<B>① プレゼンテーション層</B>（components/・screens/・App.tsx）>; style="rounded,filled"; fillcolor="#eef6ee"; color="#6aa676"; fontsize=13;
    p1 [label=<<B>レイアウト</B><BR/><FONT POINT-SIZE="9">TopBar・SideNav・ScreenFrame・PatientHeader</FONT>>, {L}];
    p2 [label=<<B>画面</B><BR/><FONT POINT-SIZE="9">ReportList・PatientInfo・CathRecord・CagLvg・Pci<BR/>PressureIvus・Pcps・Conference・Mace・Images・Restudy・Stats</FONT>>, {L}];
    p3 [label=<<B>ダイアログ・共通部品</B><BR/><FONT POINT-SIZE="9">NewReport・Master・Settings・Modal・Tabs・Panel</FONT>>, {L}];
  }}
  subgraph cluster_f {{ label=<<B>② フォームバインディング層</B>（form/）>; style="rounded,filled"; fillcolor="#f3f6fb"; color="#7d9cc4"; fontsize=13;
    f1 [label=<<B>FormProvider / Scope</B><BR/><FONT POINT-SIZE="9">編集対象と相対パスの起点を提供<BR/>"/" で始まるパスは絶対パス</FONT>>, {L}];
    f2 [label=<<B>useField(path)</B><BR/><FONT POINT-SIZE="9">値・set・変更有無(黄色)・参照のみ(ref)<BR/>・確定ロック(readOnly)を返す</FONT>>, {L}];
    f3 [label=<<B>入力部品</B>（fields.tsx）<BR/><FONT POINT-SIZE="9">TextF・NumF・SelectF・RadioF・CheckF<BR/>TripleF・DateTimeF・Calc・RefLink</FONT>>, {L}];
  }}
  subgraph cluster_a {{ label=<<B>③ アプリケーション層</B>（state/AppContext.tsx・state/screens.ts）>; style="rounded,filled"; fillcolor="#e6f0fa"; color="#5b84b1"; fontsize=13;
    a1 [label=<<B>状態</B><BR/><FONT POINT-SIZE="9">screen・draft・original・isNew<BR/>highlight・filter・patients・reports・masters</FONT>>, {L}];
    a2 [label=<<B>派生値</B><BR/><FONT POINT-SIZE="9">isDirty（draft≠original または新規）<BR/>filteredReports・form（FormApi）</FONT>>, {L}];
    a3 [label=<<B>操作</B><BR/><FONT POINT-SIZE="9">guard・goto・openReport・newReport・save<BR/>deleteReport・clearSection・changeSettings<BR/>resetSample・saveMasters・refresh</FONT>>, {L}];
  }}
  subgraph cluster_d {{ label=<<B>④ ドメイン層</B>（types/・model/・utils/calc・constants/）>; style="rounded,filled"; fillcolor="#fdf6ea"; color="#d8a25e"; fontsize=13;
    d1 [label=<<B>データモデル</B><BR/><FONT POINT-SIZE="9">types/model.ts（Patient・CathReport・Draft…）</FONT>>, {L}];
    d2 [label=<<B>既定値・補完</B><BR/><FONT POINT-SIZE="9">model/defaults.ts（createEmpty*・SECTION_FACTORIES<BR/>normalizeReport＝mergeDefaults）</FONT>>, {L}];
    d3 [label=<<B>共有項目の主画面</B><BR/><FONT POINT-SIZE="9">model/ownership.ts（OWNERSHIP・ownerOf）</FONT>>, {L}];
    d4 [label=<<B>計算・判定</B><BR/><FONT POINT-SIZE="9">utils/calc.ts（BSA・BMI・LVG・HBR・CREDO・IVUS・基準値）<BR/>utils/date.ts（年齢・日数・分）</FONT>>, {L}];
    d5 [label=<<B>選択肢・定義</B><BR/><FONT POINT-SIZE="9">constants/options.ts（項目キー・ラベル・基準範囲）</FONT>>, {L}];
  }}
  subgraph cluster_i {{ label=<<B>⑤ インフラ層</B>（storage/・utils/path・utils/id）>; style="rounded,filled"; fillcolor="#f4f4f4"; color="#9aa5a9"; fontsize=13;
    i1 [label=<<B>StorageAdapter</B><BR/><FONT POINT-SIZE="9">list/get/save/delete（患者・レポート・マスタ）<BR/>resetWithSample</FONT>>, {L}];
    i2 [label=<<B>LocalStorageAdapter</B><BR/><FONT POINT-SIZE="9">localStorage・サンプル投入</FONT>>, {L}];
    i3 [label=<<B>RemoteStorageAdapter</B><BR/><FONT POINT-SIZE="9">fetch → REST /api（3種のバックエンド）</FONT>>, {L}];
    i4 [label=<<B>パス操作</B><BR/><FONT POINT-SIZE="9">getAt・setAt（イミュータブル更新）<BR/>deepEqual・mergeDefaults・hasAnyValue</FONT>>, {L}];
  }}
  p2 -> f3 [lhead=cluster_f, label="入力欄を配置"];
  p1 -> a3 [lhead=cluster_a, label="遷移・保存・照合/確定"];
  f2 -> a2 [lhead=cluster_a, label="FormApi.set(path, v)"];
  f2 -> d3 [label="主画面か？"];
  a3 -> d2 [label="新規・クリア・読込時の補完"];
  a3 -> i1 [lhead=cluster_i, label="永続化"];
  a1 -> i4 [label="setAt / deepEqual", style=dashed];
  p2 -> d4 [label="計算欄", style=dashed];
  i1 -> i2 [style=dotted, arrowhead=empty]; i1 -> i3 [style=dotted, arrowhead=empty];
  {{rank=same; i1; i2; i3; i4;}}
}}
'''

# =====================================================================
# 5.2 編集状態の状態遷移
# =====================================================================
ST = 'shape=box, style="rounded,filled", fontsize=11, margin="0.2,0.1"'
STATE = 'digraph G {\n' + HEAD + f'''  rankdir=LR; ranksep=0.9; nodesep=0.55;
  start [shape=circle, label="", width=0.22, style=filled, fillcolor="#2c3e45"];
  none [label=<<B>レコード未選択</B><BR/><FONT POINT-SIZE="9">一覧・集計</FONT>>, {ST}, fillcolor="#f3f3f3", color="#9aa5a9"];
  clean [label=<<B>表示中（変更なし）</B><BR/><FONT POINT-SIZE="9">draft = original<BR/>保存ボタン：通常</FONT>>, {ST}, fillcolor="#e3f2e5", color="#6aa676"];
  dirty [label=<<B>変更あり</B><BR/><FONT POINT-SIZE="9">draft ≠ original<BR/>保存ボタン：赤</FONT>>, {ST}, fillcolor="#fde8e4", color="#c97b76"];
  newd [label=<<B>新規（未保存）</B><BR/><FONT POINT-SIZE="9">isNew = true<BR/>常に「変更あり」扱い</FONT>>, {ST}, fillcolor="#fde8e4", color="#c97b76"];
  ask [label=<<B>確認ダイアログ</B><BR/><FONT POINT-SIZE="9">変更が有り、修正を放棄するか</FONT>>, {ST}, fillcolor="#fff7d6", color="#c9a227"];
  hl [label=<<B>変更あり（黄色表示）</B><BR/><FONT POINT-SIZE="9">highlight = true<BR/>変更項目を黄色</FONT>>, {ST}, fillcolor="#fff3b0", color="#c9a227"];
  locked [label=<<B>確定（ロック）</B><BR/><FONT POINT-SIZE="9">status = 確定<BR/>ステータス・照合・登録者のみ変更可</FONT>>, {ST}, fillcolor="#e6ebf0", color="#7f939c"];

  start -> none;
  none -> clean [label="openReport（一覧で選択）"];
  none -> newd [label="newReport（新規作成）"];
  clean -> dirty [label="入力（set）"];
  dirty -> clean [label="save 成功\\n（original ← 保存結果）"];
  dirty -> clean [label="入力を元に戻す", style=dashed];
  newd -> clean [label="save 成功"];
  dirty -> ask [label="画面遷移・別レコード\\n（guard）"];
  newd -> ask [label="画面遷移（guard）"];
  hl -> ask [label="再度 遷移"];
  ask -> hl [label="キャンセル"];
  ask -> clean [label="放棄（draft ← original）\\n→ 遷移先へ"];
  ask -> none [label="放棄（新規は破棄）"];
  hl -> clean [label="save 成功"];
  clean -> locked [label="「確定」→ 保存"];
  locked -> clean [label="「入力中」→ 保存"];
  clean -> none [label="一覧へ（変更なし）"];
}}
'''

# =====================================================================
# 5.3 入力1件の流れ
# =====================================================================
FLOW = 'digraph G {\n' + HEAD + f'''  rankdir=LR; ranksep=0.5; nodesep=0.3;
  node [fontsize=10.5];
  u [label="利用者が入力", shape=ellipse, fillcolor="#fff7d6", color="#c9a227"];
  f1 [label=<<B>入力部品</B>（TextF 等）<BR/><FONT POINT-SIZE="9">onChange</FONT>>];
  f2 [label=<<B>useField(path)</B><BR/><FONT POINT-SIZE="9">Scope で絶対パスに解決<BR/>例 report.cathRecord.body.height</FONT>>];
  f3 [label=<<B>FormApi.set(path, v)</B>>, fillcolor="#e6f0fa", color="#5b84b1"];
  chk [label=<<B>確定ロック判定</B><BR/><FONT POINT-SIZE="9">status=確定 かつ<BR/>UNLOCKED 以外 → 無視</FONT>>, shape=diamond, fillcolor="#fff7d6", color="#c9a227", style="filled"];
  f4 [label=<<B>setDraft(setAt(draft, path, v))</B><BR/><FONT POINT-SIZE="9">イミュータブルに新しい draft</FONT>>, fillcolor="#e6f0fa", color="#5b84b1"];
  f5 [label=<<B>再描画</B><BR/><FONT POINT-SIZE="9">全入力欄が draft から値を取得</FONT>>];
  o1 [label=<<B>isDirty</B><BR/><FONT POINT-SIZE="9">deepEqual(draft, original)</FONT>>];
  o2 [label=<<B>保存ボタン赤</B>（TopBar）>, fillcolor="#fde8e4", color="#c97b76"];
  o3 [label=<<B>計算欄</B><BR/><FONT POINT-SIZE="9">BSA・BMI・EF・D2B…</FONT>>];
  o4 [label=<<B>サイドメニュー</B><BR/><FONT POINT-SIZE="9">入力ありの色（hasAnyValue）</FONT>>];
  o5 [label=<<B>黄色表示</B><BR/><FONT POINT-SIZE="9">highlight 中は value≠original の欄</FONT>>, fillcolor="#fff3b0", color="#c9a227"];
  u -> f1 -> f2 -> f3 -> chk;
  chk -> f4 [label="可"];
  f4 -> f5;
  f5 -> o1 -> o2; f5 -> o3; f5 -> o4; f5 -> o5;
}}
'''

SEQ_OPEN = '''sequenceDiagram
    autonumber
    actor U as 利用者
    participant L as ReportList / SideNav
    participant A as AppContext
    participant S as StorageAdapter
    participant F as FormProvider / 画面
    U->>L: 行の 📄・レコード送り・カテ履歴
    L->>A: openReport(id)
    A->>A: guard（変更ありなら確認ダイアログ）
    A->>S: getReport(id)・getPatient(patientRef)
    S-->>A: CathReport・Patient（normalizeReport で既定値を補完）
    A->>A: loadDraft：original = draft = {patient, report}、highlight = false
    A->>A: screen を設定（一覧からはカテ記録）
    A-->>F: form（FormApi）を提供
    F-->>U: 画面を表示（全入力欄は draft の値）
'''
SEQ_SAVE = '''sequenceDiagram
    autonumber
    actor U as 利用者
    participant T as TopBar / Ctrl+S
    participant A as AppContext
    participant S as StorageAdapter
    participant B as バックエンド（Remote 時）
    U->>T: 保存
    T->>A: save()
    A->>A: 必須チェック（患者ID・氏名・施行日）
    alt 未入力あり
        A-->>U: トースト「必須項目が未入力です」
    else OK
        A->>A: 患者の変更有無（新規 or draft.patient ≠ original.patient）
        A->>A: history に「保存（画面名）」を追加・updatedAt
        opt 患者に変更あり
            A->>S: savePatient(patient)
            S->>B: PUT /api/patients/{id}
            B-->>S: 保存結果
        end
        A->>S: saveReport(report)
        S->>B: PUT /api/reports/{id}
        B-->>S: 保存結果（version 等）
        A->>A: loadDraft（original ← 保存結果）→ 保存ボタン通常色
        A->>S: refresh（一覧・マスタ再取得）
        A-->>U: トースト「保存しました」
    end
'''


def dot(name, src):
    p = OUT / f'{name}.dot'
    p.write_text(src, encoding='utf-8')
    subprocess.run(['dot', '-Tsvg', '-o', str(OUT / f'{name}.svg'), str(p)], check=True, stderr=subprocess.DEVNULL)


def mmd(name, src):
    p = OUT / f'{name}.mmd'
    p.write_text(src, encoding='utf-8')
    pp = pathlib.Path(tempfile.mktemp(suffix='.json'))
    pp.write_text(json.dumps({'executablePath': '/usr/bin/google-chrome', 'args': ['--no-sandbox']}))
    cfg = pathlib.Path(tempfile.mktemp(suffix='.json'))
    cfg.write_text(json.dumps({'theme': 'neutral', 'themeVariables': {'fontFamily': 'Noto Sans CJK JP, sans-serif', 'fontSize': '14px'},
                               'sequence': {'mirrorActors': False, 'messageFontSize': 13, 'noteFontSize': 12, 'actorFontSize': 14}}))
    subprocess.run(['mmdc', '-i', str(p), '-o', str(OUT / f'{name}.svg'), '-p', str(pp), '-c', str(cfg), '-b', 'white'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    dot('system', SYSTEM)
    dot('components', COMP)
    dot('model', MODEL)
    dot('logic_layers', LOGIC)
    dot('state', STATE)
    dot('input_flow', FLOW)
    mmd('seq_open', SEQ_OPEN)
    mmd('seq_save', SEQ_SAVE)
    print(sorted(p.name for p in OUT.glob('*.svg')))
