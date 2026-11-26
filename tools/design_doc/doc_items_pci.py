"""PCI 画面項目一覧"""
from extra_common import G, e, table, build_doc, RELATED
from items_common import OPTS, V, L, SHARE, CALC, REP, REF, Counter, items, shot, legend, kind_legend, wrap

C = Counter('PC')
R = 'report.pci'
LS = R + '.lesions[0..4]'
LN = '病変1〜5'


def p_overview():
    return ('<h1>1. 画面の概要</h1>'
            '<p class="lead">PCI 画面は、手技全体の情報と、治療した病変（Target の列。1〜5 列で、＋で追加・✖で削除）ごとの情報を 10 のタブで記録します。'
            '病変単位の項目は <span class="code">report.pci.lesions[0..4]</span>、手技・患者単位の項目は <span class="code">report.pci</span> の下に保存します。'
            'Target（病変の部位）は全タブ共通です。</p>' +
            shot('15_pci_basic.png', 'PCI 基本タブ') +
            '<h2>タブの構成</h2>' +
            table(['タブ', '単位', 'データ', '内容'], [
                ('基本', '手技・病変', 'basic／lesions[].summary', '標的病変数・結果・合併症・ガイディング/マイクロ/GW・術前検査投薬・病変ごとの治療と術前後の狭窄度/TIMI'),
                ('病変形態', '病変', 'lesions[]', 'Type・de novo・形態（Yes/No）・屈曲・蛇行・閉塞期間・長さ・QCA（Pre/Post）・Technique・ステント理由'),
                ('Device', '病変', 'lesions[].device', 'Device 1〜10（区分・名称・サイズ・長さ・圧）・結果・Hybrid・最終 Balloon 径・ステント連続'),
                ('Bif/CTO', '病変', 'lesions[].bif／cto', '分岐部（Medina・本幹/側枝・ステント法・KBT）、CTO（Access・GW 通過法・Retrograde）、J-CTO スコア'),
                ('Complication', '病変・患者', 'lesions[].comp／patientComp／patientTreat', '手技合併症・病変への処置・最終造影所見、患者合併症・患者への処置'),
                ('J-PCI', '手技', 'jpci', 'J-PCI 登録項目（患者背景・術前検査投薬・術後投薬・PCI 基本情報・合併症・補助循環・イメージング・病変情報・退院時）'),
                ('出血・血栓リスク', '手技', 'risk', 'Staged PCI、高出血リスク（ARC-HBR）、CREDO-Kyoto 血栓リスク、ステント血栓症リスク因子、DAPT 期間'),
                ('AMI', '手技', 'ami', '発症〜最初のデバイス使用までの日時、所要時間（Door to balloon など）'),
                ('検索用', '病変', 'lesions[]', '主要項目を病変ごとに1画面で表示（データは各タブと同じ）'),
                ('参考資料', '－', '－', '分岐部病変タイプ・治療ストラテジー・Medina 分類の図（入力なし）'),
            ], widths=['24mm', '18mm', '42mm', None]) +
            '<h2>入力形式と記号</h2>' + kind_legend() + legend() +
            f'<div class="note small">{REP} の付いた病変単位の項目は Target の各列（最大 5 列）に同じ欄があります（一覧では 1 項目と数えています）。</div>')


def p_basic():
    tech = V('PCI_TECH')
    return ('<h1>2. 基本タブ</h1>' + items(C, [
        ('手技の結果', R + '.basic', [
            ('標的病変数', 'lesionCount', 'N'),
            ('サポート', 'support', 'S', V('SUPPORTS')),
            ('PCI結果', 'result', 'S', V('PCI_RESULTS')),
            ('不成功理由', 'failureReason', 'T'),
            ('合併症', 'complication', 'S', 'なし／手技関連合併症あり／出血性合併症／血管合併症／その他'),
            ('手技開始時合併症', 'startComp', 'T', '', '検索用'), ('急性期合併症', 'acuteComp', 'T', '', '検索用'),
            ('30日MACE', 'mace30', 'T', '', '検索用'), ('In Hospital合併症', 'hospComp', 'T', '', '検索用'),
            ('MDCT施行', 'mdct', 'C'), ('RI施行', 'ri', 'C'),
            ('患者単位治療', 'patientTreatment', 'TL', 'PCI／PCI+CABG／CABG／薬物療法'),
        ]),
        ('スコア・AMI', '', [
            ('Syntax・Euro・Japan Score', 'report.cagLvg.cag.syntax／euro／japan', 'N', '', REF + 'CAG と共通（編集は CAG）'),
            ('Elapsed Time', R + '.basic.elapsed', 'N', 'min'),
            ('Killip', R + '.basic.killip', 'S', 'I／II／III／IV'),
            ('Door to Balloon Time', '（計算）', 'K', 'min', CALC + 'AMI タブの病院着〜最初の device'),
        ]),
        ('使用器具', R + '.basic', [
            ('ガイディングカテーテル（名称・サイズ）', 'guiding[0..4].name／size', 'TL', 'Launcher EBU3.5 など／' + V('SHEATH_SIZES') + ' Fr', REP + '1〜5行（＋で追加・✖で削除）'),
            ('マイクロカテーテル', 'micro[0..3]', 'TL', 'デバイスマスタ（Micro）', REP + '1〜4行（＋で追加・✖で削除）'),
            ('ガイドワイヤー', 'gw[0..4]', 'TL', 'デバイスマスタ（GW）', REP + '1〜5行（＋で追加・✖で削除）'),
            ('連携パス印刷（DES／BMS／DCB）', '－', 'B', '', '地域連携パスを印刷'),
        ]),
        ('術前検査・投薬（J-PCI と共通）', R + '.jpci.pre', [
            ('術前画像・負荷検査の施行', 'imaging', 'R', V('UM_OPTS'), SHARE + 'J-PCI'),
            ('検査の種類', 'imagingItems.*', 'C', V('PREOP_IMAGING'), '「無」なら入力不可'),
            ('術前抗血小板薬の使用', 'antiplatelet', 'R', V('UM_OPTS'), SHARE),
            ('抗血小板薬', 'apItems.*', 'C', V('ANTIPLATELET')),
            ('術前抗凝固薬の使用', 'anticoag', 'R', V('UM_OPTS'), SHARE),
            ('抗凝固薬', 'acItems.*', 'C', V('ANTICOAG')),
        ]),
        (f'病変ごとの治療（表・{LN}）', LS, [
            ('Target', 'target', 'TL', '#1〜#15・HL・4AV・4PD', REP + '全タブ共通'),
            ('病変単位治療', 'summary.treatment', 'T', '', REP),
            ('治療手技', 'summary.tech.*', 'C', tech, REP + '12項目'),
            ('Pre（狭窄度）', 'summary.pre', 'N', '%', REP),
            ('Post（狭窄度）', 'summary.post', 'N', '%', REP),
            ('TIMI Pre', 'summary.timiPre', 'TL', V('TIMI'), REP),
            ('TIMI Post', 'summary.timiPost', 'TL', V('TIMI'), REP),
            ('Rentrop', 'summary.rentrop', 'TL', V('RENTROP'), REP),
            ('Comment', 'summary.comment', 'T', '', REP),
            ('Restudy非表示', 'summary.restudyHidden', 'C', '', REP + 'Restudy 画面に出さない'),
        ]),
    ]))


def p_morph():
    yn = [(lab, f'morph.{k}', 'R', 'Yes／No', REP) for k, lab in OPTS['MORPH_YN'] + OPTS['MORPH_YN2']]
    return ('<h1>3. 病変形態タブ</h1>' + shot('16_pci_lesion_morphology.png', '病変形態タブ') + items(C, [
        (f'病変形態（{LN}）', LS, [
            ('Target（血管）', 'targetSub', 'TL', 'LMT／LAD／LCX／RCA／Dx／OM／PL／PD／SVG／ITA', REP + '＋で病変（列）を追加、✖で削除して後ろを詰める（全タブ共通）'),
            ('Type', 'type', 'TL', V('LESION_TYPES'), REP + 'ACC/AHA 分類'),
            ('Type の自動提案', '（計算）', 'K', 'A／B1／B2／C', REP + CALC + '形態から提案。「適用」で Type に反映。入力と異なると赤字'),
            ('de novo…（大分類）', 'deNovoMajor', 'TL', V('DENOVO_MAJOR'), REP),
            ('de novo…（小分類）', 'deNovoMinor', 'TL', V('DENOVO_MINOR'), REP),
            *yn,
            ('Angulation', 'angulation', 'TL', V('ANGULATION'), REP),
            ('ProximalTortuosity', 'proximalTortuosity', 'TL', V('TORTUOSITY'), REP),
            ('Age of Occlusion', 'ageOfOcclusion', 'TL', '<1ヶ月／1-3ヶ月／>3ヶ月／不明', REP),
            ('Branch Protection', 'branchProtection', 'TL', 'GW／Balloon／Stent／なし', REP),
            ('Length（mm）', 'lengthA', 'N', 'mm', REP),
            ('Length（区分）', 'lengthB', 'TL', '<10mm／10-20mm／>20mm', REP),
            ('Pre Ref・%DS・MLD', 'pre.ref／pct／mld', 'N', 'mm／%／mm', REP + CALC + '「取得」で Pressure/IVUS の QCA から'),
            ('Post Ref・%DS・MLD', 'post.ref／pct／mld', 'N', 'mm／%／mm', REP + CALC + '同上（post PCI の列）'),
            ('Technique', 'technique', 'TL', 'Direct stenting／Pre-dilatation／POBA／DCB only／Atherectomy+Stent', REP),
            ('BMS選択の理由（1・2）', 'bmsReason1／bmsReason2', 'TL', '出血リスク／DAPT継続困難／手術予定／大血管径', REP),
            ('Reason of Stenting', 'stentingReason', 'TL', 'de novo lesion／Bail out／Suboptimal result／Dissection', REP),
            ('Method of Stenting', 'stentingMethod', 'TL', 'Angio guided／IVUS guided／OCT guided／Physiology guided', REP),
        ]),
    ]) + '<p class="small">各項目の定義と標準（ACC/AHA・SYNTAX・J-CTO・TIMI など）との対応は「CAG・PCI 病変形態・所見の整理」を参照。</p>')


def p_device():
    return ('<h1>4. Device タブ</h1>' + items(C, [
        (f'Device（{LN}）', LS + '.device', [
            ('病変形態(post)', 'morphPost', 'T', '', REP),
            ('Device1〜10：区分', 'items[0..9].category', 'TL', V('DEVICE_CATEGORIES'), REP + '10行'),
            ('Device1〜10：名称', 'items[0..9].name', 'TL', 'デバイスマスタ（区分で絞込み）', REP),
            ('Device1〜10：サイズ・長さ・圧', 'items[0..9].size／length／pressure', 'N', 'mm／mm／atm', REP),
            ('理由', 'reason', 'T', '', REP),
            ('結果', 'result', 'TL', V('PCI_RESULTS'), REP),
            ('DESs Hybrid', 'desHybrid', 'R', 'Yes／No', REP),
            ('DES-BMS Hybrid', 'desBmsHybrid', 'R', 'Yes／No', REP),
            ('Reason for failure', 'failureReason', 'TL', 'GW不通過／Device不通過／解離／穿孔／その他', REP),
            ('Rota burr size', 'rotaBurr', 'TL', '1.25／1.5／1.75／2.0／2.15', REP),
            ('Protection Device', 'protection', 'TL', 'Filtrap／Parachute／なし', REP),
            ('最終Balloon径・総Stent長・MaxPress', 'final.balloon／stentLen／maxPress', 'N', 'mm／mm／atm',
             REP + CALC + '「算出」：Balloon 系の最大径、DES/BMS の長さの合計、最大圧'),
            ('stent連続：有無・連続総長・連続総数', 'overlap.connected／totalLen／count', 'TL／N', '有／無、mm、本', REP + '連結した場合は中枢側の病変のみに記載'),
        ]),
    ]))


def p_bifcto():
    return ('<h1>5. Bif/CTO タブ</h1>' + items(C, [
        (f'Bifurcation（{LN}）', LS + '.bif', [
            ('Main/Side branch（Medina）', 'mainSide', 'TL', 'Medina 1,1,1／1,1,0／1,0,1／0,1,1／1,0,0／0,1,0／0,0,1', REP),
            ('Main branch：血管・処置', 'main.a／main.b', 'TL', 'LAD／LCX／RCA／LMT、Stent／Balloon／GW only', REP),
            ('Side branch：血管・処置', 'side.a／side.b', 'TL', 'Dx／OM／PL／PD／LCX／Septal、Stent／Balloon／GW only／なし', REP),
            ('Bifurcation Stent', 'stent', 'TL', V('BIF_STENTS'), REP),
            ('Add Procedure', 'addProcedure', 'TL', 'KBT／POT／POT-side-POT／Re-POT／DCB to SB', REP),
            ('Fate of SB', 'fateSB', 'TL', 'TIMI3／TIMI2／TIMI1／TIMI0／閉塞', REP),
            ('KBT：Balloon 径（MB・SB）・圧', 'kbt.mb／kbt.sb／kbt.pressure', 'N', 'mm／mm／atm', REP),
        ]),
        (f'CTO（{LN}）', LS + '.cto', [
            ('閉塞期間', 'duration', 'S', '3か月未満／3か月以上／不明', REP + '旧「Age of Occlusion」から自動補完'),
            ('J-CTO：入口部が鈍・石灰化・屈曲 >45°・閉塞長 ≥20mm・再挑戦', 'jcto.{blunt,calc,bend,len20,retry}', 'R', 'Yes／No', REP + '5 項目'),
            ('J-CTO スコア（病変）', '（計算）', 'K', '0〜5 点', REP + CALC + '5 項目すべて回答で表示'),
            ('Access', 'access', 'TL', V('CTO_ACCESS'), REP),
            ('Method of GW passing', 'gwMethod', 'TL', V('GW_METHOD'), REP),
            ('Parallel wire', 'parallelWire', 'R', 'Yes／No', REP),
            ('Retro：Access', 'retro.access', 'TL', 'Septal／Epicardial／Graft', REP),
            ('Retro：GC（名称・サイズ）', 'retro.gc.name／size', 'TL', 'EBU3.5／EBU3.75／AL1／JR4／SAL1、' + V('SHEATH_SIZES'), REP),
            ('Retro：GW', 'retro.gw', 'TL', 'Sion／Suoh 03／Fielder XT-R／Gaia Next', REP),
            ('Retro：Vessel', 'retro.vessel', 'TL', 'LAD／LCX／RCA', REP),
            ('Retro：Channel', 'retro.channel', 'TL', 'Septal CC／Epicardial CC／Atrial', REP),
            ('Retro：Channel Passing Wire', 'retro.channelWire', 'T', '', REP),
        ]),
        ('CTO スコア', R, [('CTO Score（J-CTO・手技全体）', 'ctoScore', 'N', '0〜5', '「病変の最大値を反映」ボタン')]),
    ]))


def p_comp():
    rows = []
    for g in OPTS['COMP_LESION']:
        rows.append((f'{g["title"].strip("<>")}（{LN}）', LS + '.comp',
                     [(lab, k, 'R', 'Yes／No', REP) for k, lab in g['items']]))
    return ('<h1>6. Complication タブ</h1>' + items(C, rows + [
        ('Specific procedure', R, [('Specific procedure', 'specificProcedure', 'T')]),
        ('Patient complication', R + '.patientComp', [(lab, k, 'R', 'Yes／No') for k, lab in OPTS['COMP_PATIENT']]),
        ('Treatment to patient', R + '.patientTreat', [(lab, k, 'R', 'Yes／No') for k, lab in OPTS['TREAT_PATIENT']]),
    ]))


def p_jpci():
    J = R + '.jpci'
    return ('<h1>7. J-PCI タブ</h1>'
            '<p class="lead">J-PCI レジストリ（CVIT）の登録項目です。カテ記録・AMI タブ・病変タブの値は共通データとして表示します。</p>' + items(C, [
        ('患者背景', J + '.bg', [
            *[(lab, f'report.cathRecord.risk.{k}', 'R', V('UMU_OPTS'), REF + 'カテ記録と共通（編集はカテ記録）') for k, lab in OPTS['JPCI_BG_UMU_LEFT']],
            *[(f'24時間以内の{lab}', k, 'R', V('UMU_OPTS')) for k, lab in OPTS['JPCI_BG_24H']],
            ('一ヶ月以内の症状の有無', 'symptom1m', 'S', V('SYMPTOMS_1M')),
            ('今回入院に至った診断名', 'admitDx', 'S', V('JPCI_DX')),
            ('その他', 'other', 'T'),
            ('Door to balloon Time', '（計算）', 'K', 'min', CALC + 'ST上昇型 AMI のみ。AMI タブから'),
            ('併発疾患', 'comorbid', 'R', '無／不明'),
            ('ステント血栓症', 'stentThrombosis', 'C'),
            ('DM・HT・HD・HL', 'report.cathRecord.risk.*', 'R', V('PM_OPTS'), REF + 'カテ記録と共通'),
            ('喫煙（過去1年以内）', 'smoking', 'R', V('JPCI_SMOKING_OPTS')),
            ('維持透析', 'dialysis', 'R', V('PM_OPTS')),
            ('末梢血管障害（AAA/PAD）', 'report.cathRecord.risk.pad', 'R', V('PM_OPTS'), REF + 'カテ記録と共通'),
            ('腎不全', 'report.cathRecord.risk.renal', 'R', V('PM_OPTS'), REF + 'カテ記録と共通'),
            ('慢性肺疾患（COPD）', 'report.cathRecord.risk.copd', 'R', V('PM_OPTS'), REF + 'カテ記録と共通'),
            ('Hb・Cr', 'report.cathRecord.labs.cbc.Hb／admission.Cr', 'N', 'g/dL／mg/dL', REF + 'カテ記録と共通'),
            ('標的病変数', 'lesionCount', 'N'),
            ('左主幹部病変', 'lmt', 'R', V('UM_OPTS')),
            ('大動脈疾患（有無・内容）', 'aortic／aorticText', 'C／T'),
        ]),
        ('術前検査・投薬', J + '.pre', [
            ('術前画像・負荷検査・抗血小板薬・抗凝固薬', 'imaging／antiplatelet／anticoag ほか', 'R／C', '基本タブと同じ', SHARE + '基本タブ（2章）と共通'),
            ('非侵襲的FFR-CT実測値', 'ffrCt', 'N'),
            ('FFR（施行・実測値）', 'ffr／ffrValue', 'C／N'),
            ('Resting index（施行・実測値）', 'ri／riValue', 'C／N'),
            ('旧項目：抗凝固薬', 'legacy.*', 'C', V('ANTICOAG_LEGACY'), '過去データ用'),
        ]),
        ('術後情報（PCI後投薬）', J + '.post', [
            ('抗血栓薬', 'antithrombotic.*', 'C', V('POST_ANTITHROMBOTIC')),
            ('抗血栓薬なし', 'antithromboticNone', 'C'),
            ('抗脂質薬', 'lipid.*', 'C', V('POST_LIPID')),
            ('抗脂質薬なし', 'lipidNone', 'C'),
        ]),
        ('PCI基本情報', J + '.info', [
            ('JPCI術者', 'jpciOperator', 'TL', '医師マスタ'),
            ('第一術者・会員番号', 'firstOp／firstOpNo', 'TL／T', '医師マスタ'),
            ('指導医の有無', 'supervisor', 'R', V('UMU_OPTS')),
            ('指導医・会員番号', 'supervisorName／supervisorNo', 'TL／T', '医師マスタ'),
            ('PCIのステータス', 'status', 'R', V('URGENCY_OPTS')),
            ('透視時間・造影剤・造影剤量', 'report.cathRecord.exam.fluoroTime／contrast', 'N／TL', '分、ml', REF + 'カテ記録と共通'),
            ('アクセスサイト', 'accessSite', 'TL', '橈骨動脈／遠位橈骨動脈／大腿動脈／上腕動脈'),
            ('手技に関連する合併症', 'procComp', 'R', V('UMU_OPTS')),
            ('合併症の内容', 'compItems.*', 'C', V('JPCI_COMP'), '「無」なら入力不可'),
            ('(非アクセスサイトの場合)', 'nonAccessSite', 'C'),
            ('院内死亡日・死因', 'deathDate／deathCause', 'D／T'),
            ('補助循環デバイスの使用', 'mcs', 'R', V('UM_OPTS')),
            ('補助循環デバイス', 'mcsItems.*', 'C', V('MCS_ITEMS')),
            ('補助循環のタイミング', 'mcsTiming.*', 'R', V('TIMING_OPTS'), 'デバイスごと'),
            ('血管内イメージングの使用', 'imaging', 'R', V('UM_OPTS')),
            ('イメージングデバイス', 'imagingItems.*', 'C', V('IMAGING_ITEMS')),
        ]),
        ('PCI病変情報', LS, [
            ('病変性状', '（表示）', 'K', '', CALC + 'Type・de novo・CTO・分岐部から表示'),
            ('成否', 'success', 'S', 'Success／Failure', REP),
            ('成否の自動判定', '（計算）', 'K', 'Success／Failure', REP + CALC + '術後の残存狭窄 ≤25% かつ TIMI 3 → Success。「適用」で反映'),
            ('使用機器', '（表示）', 'K', '', CALC + 'Device タブから表示'),
        ]),
        ('退院時情報', J + '.discharge', [('PCI結果', 'pciResult', 'TL', '成功／不成功／部分成功')]),
    ]))


def p_risk():
    return ('<h1>8. 出血・血栓リスクタブ</h1>' + items(C, [
        ('Staged PCI', R + '.risk', [('Staged PCI', 'staged', 'C'), ('内容', 'stagedText', 'T', '', 'チェックした時のみ')]),
        ('高出血リスク：主要項目', R + '.risk.hbrMajor', [(lab, k, 'C') for k, lab in OPTS['HBR_MAJOR']]),
        ('高出血リスク：副次項目', R + '.risk.hbrMinor', [(lab, k, 'C') for k, lab in OPTS['HBR_MINOR']]),
        ('判定', '', [('High Bleeding Risk', '（計算）', 'K', 'HBR／non-HBR', CALC + '主要 1 つ以上 または 副次 2 つ以上で HBR')]),
        ('血栓リスク（CREDO-Kyoto）', R + '.risk.credo', [(lab, k, 'C', f'{p} 点') for k, lab, p in OPTS['CREDO_ITEMS']] + [
            ('血栓リスクスコア', '（計算）', 'K', '0〜12 点', CALC + '0〜1 低・2〜3 中・4 以上 高リスク'),
        ]),
        ('ステント血栓症リスク因子', R + '.risk.st', [(lab, k, 'C') for k, lab in OPTS['ST_RISK']]),
        ('方針', R + '.risk', [('DAPT推奨期間', 'daptMonths', 'N', 'ヶ月'), ('Memo', 'memo', 'A')]),
    ]))


def p_ami():
    steps = [('onset', '発症'), ('call', '入電・覚知(119番)'), ('sceneArr', '現場着'), ('sceneDep', '現場発'), ('hospArr', '病院着'), ('cathLab', 'カテ室入室'), ('firstDevice', '最初のdevice使用')]
    return ('<h1>9. AMI タブ</h1>' + items(C, [
        ('日時', R + '.ami', [(lab, f'{k}.date／time', 'DT') for k, lab in steps]),
        ('所要時間（計算）', '', [
            ('入電 − 病院着時間', '（計算）', 'K', '分', CALC + '入電→病院着'),
            ('Onset to balloon時間', '（計算）', 'K', '分', CALC + '発症→最初の device'),
            ('Door to balloon時間', '（計算）', 'K', '分', CALC + '病院着→最初の device。90 分超はピンク。基本・J-PCI タブにも表示'),
            ('病院着 − カテ室入室時間', '（計算）', 'K', '分', CALC),
            ('STEMI時間経過シート', '－', 'B', '', '時間経過の図と表を表示・印刷'),
        ]),
    ]) + '<h1>10. 検索用・参考資料タブ</h1>'
         '<p class="lead">検索用タブは、病変ごと（病変1〜5 の小タブ）に主要項目を1画面に並べたものです。新しいデータは持たず、他のタブと同じ項目を表示・編集します。</p>' +
            table(['検索用タブの欄', '元のタブ・データ'], [
                ('Target・治療手技（10項目）・Pre・Post・TIMI・Comment', '基本タブ（summary.*）'),
                ('Type・de novo・形態（Yes/No）・Angulation・ProximalTortuosity・Age of Occlusion・Branch Protection', '病変形態タブ'),
                ('Ref. Length（lengthA・pre.ref）・Pre/Post %・MLD・Technique・BMS選択の理由', '病変形態タブ'),
                ('病変形態(post)・Device1〜7・理由・結果', 'Device タブ'),
                ('ICT or IVT・血栓溶解剤・投与量・結果', '検索用タブのみで表示（lesions[].ict.type／agent／dose／result）'),
                ('TIMI Pre・TIMI Post', '基本タブ（summary.timiPre／timiPost）'),
            ], widths=['100mm', None]) +
            items(C, [(f'ICT/IVT（{LN}）', LS + '.ict', [
                ('ICT or IVT', 'type', 'TL', 'ICT／IVT', REP),
                ('血栓溶解剤', 'agent', 'TL', 'ウロキナーゼ／t-PA／モンテプラーゼ', REP),
                ('投与量', 'dose', 'T', '', REP),
                ('結果', 'result', 'T', '', REP),
            ])]) +
            '<p class="small">参考資料タブ（分岐部病変タイプ・分岐部治療ストラテジー・Medina 分類）は図の表示のみで、入力項目はありません。</p>')


def p_links():
    return ('<h1>11. 他画面との連携・自動計算・項目数</h1>' +
            table(['項目', '関係する画面・データ', '内容'], [
                ('Syntax・Euro・Japan Score', 'CAG（report.cagLvg.cag）', 'PCI 基本タブでは参照のみ'),
                ('DM・HT・HD・HL・Hb・Cr・透視時間・造影剤', 'カテ記録（report.cathRecord）', 'J-PCI タブで同じ値を表示・編集'),
                ('術前検査・投薬', 'jpci.pre', '基本タブと J-PCI タブで同じデータ'),
                ('Pre/Post Ref・%DS・MLD', 'Pressure/IVUS の QCA', '「取得」ボタン：Target が一致し、phase が pre/post の列から'),
                ('Door to balloon', 'AMI タブ', '基本タブ・J-PCI タブに表示'),
                ('Target の候補', 'CAG のセグメント', '#1〜#15・HL・4AV・4PD'),
                ('病変性状・使用機器', '病変形態・Device タブ', 'J-PCI の病変情報に自動表示'),
                ('デバイス名の候補', 'デバイスマスタ', 'GW・Micro・Device の名称（「デバイスマスタを編集」）'),
                ('Restudy非表示', 'Restudy 画面', 'チェックした病変は Restudy に出さない'),
            ], widths=['50mm', '48mm', None]) +
            '<h2>自動計算の一覧</h2>' +
            table(['項目', '計算'], [
                ('最終Balloon径', 'Device の区分が Balloon・NC・Scoring・Cutting・DCB のサイズの最大'),
                ('総Stent長', '区分 DES・BMS の長さの合計'),
                ('MaxPress', '全 Device の圧の最大'),
                ('High Bleeding Risk', '主要項目 ≥1 または 副次項目 ≥2 → HBR'),
                ('CREDO-Kyoto スコア', 'CKD・AF・PVD・貧血 各2点、75歳以上・心不全・DM・CTO 各1点（0〜12）'),
                ('AMI の所要時間', '日付＋時刻の差（分）'),
                ('ACC/AHA Type の提案', 'C の特徴（>20mm・高度蛇行・屈曲 >90°・3か月以上の閉塞）が1つでも→C、B の特徴 2つ以上→B2、1つ→B1、なし→A'),
                ('J-CTO スコア', '5 項目の Yes の数（0〜5）'),
                ('病変成功', '術後の残存狭窄（QCA を優先）≤25% かつ TIMI 3'),
            ], widths=['42mm', None]) +
            '<h2>入力の制御</h2>' +
            table(['条件', '動作'], [
                ('タブにデータあり', 'タブ名に印。基本〜J-PCI は矢印付き（入力の順番）'),
                ('「無」を選んだ項目（術前投薬・合併症など）', '内訳のチェック欄が入力不可'),
                ('病変の ✖（病変形態タブ）', '確認のうえ、その病変の全タブの入力をクリア'),
            ], widths=['70mm', None]) +
            '<h2>項目数</h2>' + table(['区分', '項目数'], [(k, (str(v), 'r')) for k, v in C.per.items()] + [(('合計', 'k'), (str(C.n), 'r k'))], widths=[None, '24mm']))


PARTS = [
    ('ov', 1, '1. 画面の概要', p_overview),
    ('ba', 1, '2. 基本タブ', p_basic),
    ('mo', 1, '3. 病変形態タブ', p_morph),
    ('de', 1, '4. Device タブ', p_device),
    ('bc', 1, '5. Bif/CTO タブ', p_bifcto),
    ('cp', 1, '6. Complication タブ', p_comp),
    ('jp', 1, '7. J-PCI タブ', p_jpci),
    ('rk', 1, '8. 出血・血栓リスクタブ', p_risk),
    ('am', 1, '9. AMI タブ／10. 検索用・参考資料タブ', p_ami),
    ('ln', 1, '11. 他画面との連携・自動計算・項目数', p_links),
]

if __name__ == '__main__':
    build_doc('PCI 項目一覧', 'PCI 画面（10 タブ）の項目・データパス・入力形式・選択肢・連携', 'React 版「PCI」画面（report.pci）',
              RELATED, wrap(PARTS), G.ROOT / 'docs/design/items_pci.pdf')
