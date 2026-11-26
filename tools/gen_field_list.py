#!/usr/bin/env python3
"""全入力項目一覧（Excel）を生成
  1) データ構造（frontend/src/model/defaults.ts の既定値）から全項目パスを抽出 … /tmp/dump.json
  2) 画面ソース（*.tsx）の入力コンポーネントから 日本語ラベル・入力形式・選択肢・単位 を抽出
  3) constants/options.ts の定義（ラベル・基準値）で補完
usage: python3 tools/gen_field_list.py [/tmp/dump.json] [out.xlsx]
"""
import json, re, sys, pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'frontend/src'
dump = json.load(open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/dump.json', encoding='utf-8'))
LEAVES, ARRLEN, C = dump['leaves'], dump['arrLen'], dump['consts']

# ------------------------------------------------------------------ JSX 解析
COMP = {'TextF': '文字入力', 'NumF': '数値入力', 'DateF': '日付', 'TimeF': '時刻', 'SelectF': 'プルダウン', 'RadioF': 'ラジオボタン',
        'CheckF': 'チェックボックス', 'TextAreaF': '複数行テキスト', 'TripleF': '3値入力(収縮期/拡張期/平均)', 'DateTimeF': '日付＋時刻',
        'CellRadio': 'ラジオボタン(表)', 'CellCheck': 'チェックボックス(表)', 'LabF': '数値入力(検査値)'}
jsx = []  # (file, comp, pathpattern(regex), attrs)
for f in SRC.rglob('*.tsx'):
    t = f.read_text(encoding='utf-8')
    for m in re.finditer(r'<(%s)\b((?:[^<>]|=>|<[A-Za-z/][^<>]*>)*?)/>' % '|'.join(COMP), t, re.S):
        comp, attrs = m.group(1), m.group(2)
        pm = re.search(r'path=(?:"([^"]+)"|\{`([^`]+)`\}|\{\'([^\']+)\'\})', attrs)
        if not pm:
            continue
        p = next(g for g in pm.groups() if g is not None)
        def attr(name, lit=False):
            mm = re.search(r'\b' + name + r'=(?:"([^"]*)"|\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\})', attrs)
            if not mm:
                return None
            if lit:
                return mm.group(1)
            return mm.group(1) if mm.group(1) is not None else '{' + mm.group(2) + '}'
        if attr('type', True) == 'time':
            comp = 'TimeF'
        if all('${' in seg for seg in p.lstrip('/').split('.')):
            continue  # 全セグメントが変数のパスは特定できないため除外
        jsx.append(dict(file=str(f.relative_to(SRC)), comp=comp, path=p, label=attr('label'), options=(attr('options') or attr('list') or '').strip('{}') or None,
                        unit=attr('unit', True), ph=attr('placeholder', True)))
    # PCI 病変グリッドの行定義 { label: 'X', render: (i) => txt(`...`) / yn(`...`) }
    for m in re.finditer(r"label:\s*'([^']+)'[^}]*?\b(txt|yn)\(`([^`]+)`(?:,\s*([^)]+))?\)", t):
        jsx.append(dict(file=str(f.relative_to(SRC)), comp='RadioF' if m.group(2) == 'yn' else 'TextF', path=m.group(3), label=m.group(1),
                        options='O.YN_OPTS' if m.group(2) == 'yn' else (m.group(4) or None), unit=None, ph=None))
    # <KV label="X"> ... path="..." ... </KV>（検索用タブ）
    for m in re.finditer(r'<KV[^>]*label="([^"]+)"[^>]*>(.*?)</KV>', t, re.S):
        for pm in re.finditer(r'<(\w+)\s+path=(?:"([^"]+)"|\{`([^`]+)`\})', m.group(2)):
            jsx.append(dict(file=str(f.relative_to(SRC)), comp=pm.group(1), path=pm.group(2) or pm.group(3), label=m.group(1), options=None, unit=None, ph=None))

def pat(p):
    """JSXのパス → 正規表現（${...} は任意セグメント、/ 始まりは絶対）"""
    p = p.lstrip('/')
    parts = [r'[^.]+' if '${' in seg else re.escape(seg) for seg in p.split('.')]
    return re.compile(r'(^|\.)' + r'\.'.join(parts) + '$')

for j in jsx:
    j['re'] = pat(j['path'])
    if j['comp'] == 'TripleF':
        j['re'] = re.compile(pat(j['path']).pattern[:-1] + r'\.(s|d|m)$')
    if j['comp'] == 'DateTimeF':
        j['re'] = re.compile(pat(j['path']).pattern[:-1] + r'\.(date|time)$')

# ------------------------------------------------------------------ 定数ラベル
def kl(*names):
    out = {}
    for n in names:
        for row in C[n]:
            out[row[0]] = row[1] if not isinstance(row, dict) else row['label']
    return out

def labdefs(*names):
    out = {}
    for n in names:
        for row in C[n]:
            k, label, unit = row[0], row[1], row[2]
            lo = row[3] if len(row) > 3 else None
            hi = row[4] if len(row) > 4 else None
            rng = f'基準 {"" if lo is None else lo}〜{"" if hi is None else hi}' if (lo is not None or hi is not None) else ''
            out[k] = (label, unit, rng)
    return out

SEG = {s['key']: s['label'] if not s['label'].isdigit() and s['label'] not in ('4AV', '4PD') else s['key'] for s in C['CAG_SEGMENTS']}
OPTS = lambda name: ' / '.join((o['label'] if isinstance(o, dict) else str(o)) if not isinstance(o, list) else o[1] for o in C[name]) if name in C else ''
TRIPLE = {'s': '収縮期', 'd': '拡張期', 'm': '平均'}
DT = {'date': '日付', 'time': '時刻'}
STEPS = {'onset': '発症', 'call': '入電・覚知(119番)', 'sceneArr': '現場着', 'sceneDep': '現場発', 'hospArr': '病院着', 'cathLab': 'カテ室入室',
         'firstDevice': '最初のdevice使用', 'arrest': '心停止時間', 'start': 'PCPS開始'}

# パス末尾 → ラベル（JSX でラベルが取れない項目の補完）
MANUAL = {
    'patient.id': '内部ID', 'patient.createdAt': '作成日時', 'patient.updatedAt': '更新日時',
    'report.id': 'レポートID', 'report.patientRef': '患者参照(patients._id)', 'report.status': 'ステータス(入力中/確定)', 'report.verified': '照合済',
    'report.createdAt': '作成日時', 'report.updatedAt': '更新日時', 'report.header.registrant': '登録者',
    'report.header.qca': 'QCA', 'report.history[].at': '登録日時', 'report.history[].by': '登録者', 'report.history[].action': '操作内容',
    'admissions[].admitDate': '入院日', 'admissions[].dischargeDate': '退院日', 'admissions[].doctor': '入院主治医', 'admissions[].diagnosis': '診断', 'admissions[].summary': '要約',
    'collaterals[].from': '送達元', 'collaterals[].to': '送達先', 'collaterals[].grade': 'J（Rentrop分類）', 'collaterals[].state': 'State（状態）',
    'grafts[].graft': 'グラフト名称', 'grafts[].anastomosis': '吻合部', 'grafts[].patency': '通行状態',
    'guiding[].name': 'ガイディングカテーテル 名称', 'guiding[].size': 'ガイディングカテーテル サイズ(Fr)', 'basic.micro[]': 'マイクロカテーテル', 'basic.gw[]': 'ガイドワイヤー',
    'items[].category': 'デバイス 種別', 'items[].name': 'デバイス 名称', 'items[].size': 'サイズ', 'items[].length': '長さ', 'items[].pressure': '圧',
    'lesions[].target': 'Target（病変部位）', 'lesions[].targetSub': 'Target（血管）', 'lesions[].success': '成否',
    'summary.treatment': '病変単位治療', 'summary.pre': 'Pre(%)', 'summary.post': 'Post(%)', 'summary.timiPre': 'TIMI Pre', 'summary.timiPost': 'TIMI Post',
    'summary.rentrop': 'Rentrop', 'summary.comment': 'Comment', 'summary.restudyHidden': 'Restudy非表示',
    'pre.ref': 'Pre Ref.', 'pre.pct': 'Pre %', 'pre.mld': 'Pre MLD', 'post.ref': 'Post Ref.', 'post.pct': 'Post %', 'post.mld': 'Post MLD',
    'lengthA': 'Length(mm)', 'lengthB': 'Length(区分)', 'deNovoMajor': 'de novo 大分類', 'deNovoMinor': 'de novo 小分類',
    'bmsReason1': 'BMS選択の理由1', 'bmsReason2': 'BMS選択の理由2',
    'final.balloon': '最終Balloon径', 'final.stentLen': '総Stent長', 'final.maxPress': 'MaxPress', 'overlap.connected': 'stent連続',
    'overlap.totalLen': '連続総長', 'overlap.count': '連続総数', 'device.reason': '理由', 'device.result': '結果',
    'main.a': 'Main branch（血管）', 'main.b': 'Main branch（処置）', 'side.a': 'Side branch（血管）', 'side.b': 'Side branch（処置）',
    'kbt.mb': 'KBT Balloon径(MB)', 'kbt.sb': 'KBT Balloon径(SB)', 'kbt.pressure': 'KBT Pressure', 'retro.gc.name': 'Retro GC', 'retro.gc.size': 'Retro GC サイズ',
    'ict.type': 'ICT or IVT', 'ict.agent': '血栓溶解剤', 'ict.dose': '投与量', 'ict.result': '結果',
    'pressure[].lesion': '病変', 'pressure[].phase': '病変区分(診断のみ/pre PCI/post PCI)', 'pressure[].drug': '薬剤', 'pressure[].dominancy': 'Dominancy',
    'pressure[].priorMI': 'prior MI(+,-)', 'pressure[].priorMISite': 'prior MI site', 'pressure[].stent': 'Stent(+,-)', 'pressure[].stentLesion': 'Stent Lesion',
    'prevPci[].date': '施行日', 'prevPci[].site': '部位', 'prevPci[].device': 'デバイス', 'prevPci[].note': '備考',
    '[].drug': '薬剤名', '[].dose': '用量', '[].usage': '用法', '[].days': '日数',
    'restudy.lesions[].segment': '病変', 'restudy.lesions[].prevPct': '前回Post(%)', 'restudy.lesions[].currPct': '今回(%)', 'restudy.lesions[].lateLoss': 'Late loss(mm)',
    'restudy.lesions[].restenosis': '再狭窄', 'restudy.lesions[].tlr': 'TLR', 'restudy.lesions[].comment': 'コメント',
    'images[].id': '画像ID', 'images[].fileName': 'ファイル名', 'images[].mimeType': 'MIMEタイプ', 'images[].dataUrl': '画像データ(Base64)',
    'mace[].death.checked': '全死亡', 'mace[].acs.checked': '非致死性ACS', 'mace[].stroke.checked': '非致死性脳梗塞', 'mace[].hf.checked': '非致死性心不全',
    'mace[].bleeding.checked': '非致死性出血', 'mace[].revasc.checked': '血行再建', 'mace[].other.checked': 'その他・ACS複数回症例',
    'mace[].negative.checked': 'PCI後MACE(−)確認', 'mace[].positive.checked': 'PCI後MACE(+)', 'mace[].other.text': 'その他 内容',
    'cathRecord.exam.purposes.followUp': 'Follow-up', 'cathRecord.exam.purposes.other1': 'その他1', 'cathRecord.exam.purposes.other2': 'その他2',
    'cathRecord.exam.other1Text': 'その他1 内容', 'cathRecord.exam.other2Text': 'その他2 内容', 'exam.sheath.name': 'シース', 'exam.sheath.size': 'シースサイズ(Fr)',
    'exam.contrast.agent': '造影剤', 'exam.contrast.volume': '造影使用量(ml)', 'exam.flags.ccuHotline': 'CCUホットライン', 'exam.flags.impressiveCase': 'ImpressiveCase',
    'doctors.operators[]': '術者（3名）', 'doctors.assistants[]': '助手（3名）', 'pcps.operators[]': '術者（3名）',
    'arterySheath.name': 'Artery シース名称', 'arterySheath.size': 'Artery シースサイズ(Fr)', 'veinSheath.name': 'Vein シース名称', 'veinSheath.size': 'Vein シースサイズ(Fr)',
    'conference.notPerformed.basic': '検査未実施（基本）', 'jpci.info.nonAccessSite': '非アクセスサイトの場合', 'lvg.aog.performed': 'AOG施行',
    'labs.hbs.date': 'HBs 検査日', 'labs.hcv.date': 'HCV 検査日', 'labs.dischargeDate': '退院時 採血日',
    'treadmill.findings': '所見', 'exam.followUpReason': 'Follow-up 理由', 'lvg.aog.findings': 'AOG 所見', 'lvg.aog.ar': 'AOG AR (Sellers)', 'exam.urgency': '待機/緊急', 'prognosis.angioFuExclude2': 'AngioFU対象外理由2', 'other.study1': 'Study1', 'other.study2': 'Study2',
    'risk.smokingPerDay': '喫煙 本/日', 'risk.smokingStartAge': '喫煙 開始年齢', 'risk.smokingQuitAge': '喫煙 禁煙年齢',
    'risk.eSmokingPerDay': '電子煙草 本/日', 'risk.eSmokingStartAge': '電子煙草 開始年齢', 'risk.eSmokingQuitAge': '電子煙草 禁煙年齢',
    'cathRecord.pciSummary': 'PCIサマリー/連絡事項', 'cathRecord.futurePlan': '今後の方針', 'cathRecord.comment': 'Comment',
    'jpci.bg.aorticText': '大動脈疾患 内容', 'jpci.pre.imaging': '術前画像・負荷検査の施行', 'jpci.pre.antiplatelet': '術前抗血小板薬の使用',
    'jpci.pre.anticoag': '術前抗凝固薬の使用', 'jpci.info.mcs': '補助循環デバイスの使用', 'jpci.info.imaging': '血管内イメージングデバイスの使用',
    'risk.stagedText': 'Staged PCI 内容', 'pressureIvus.lesions[].site': '対象部位', 'conference.history.past': '既往歴（予備：画面は患者情報の既往歴を使用）',
    'pressureIvus.lesions[].device': 'カテーテル', 'pressureIvus.lesions[].comment': 'コメント', 'cag.comment': 'Comment', 'lvg.comment': 'LVG Comment',
    'conference.comment': 'コメント', 'conference.onsetCourse': 'Onset and Course', 'patient.allergy.contrastDetail': '造影剤アレルギー 詳細',
    'patient.allergy.drugDetail': '薬剤アレルギー 薬剤名', 'scinti.findings': '所見', 'mdct.findings': '所見',
}

def manual(path):
    p = re.sub(r'\.\d+', '[]', path)
    for k in sorted(MANUAL, key=len, reverse=True):
        if p == k or p.endswith('.' + k) or p.endswith(k) and k.startswith('['):
            return MANUAL[k]
    return None

# ------------------------------------------------------------------ 画面・区分
def screen(p):
    s = p.split('.')
    if s[0] == 'patient':
        return ('全画面ヘッダ／患者情報入力' if s[1] in ('patientId', 'name', 'kana', 'sex', 'birthDate') else '患者情報入力'), group_patient(s[1])
    if s[1] == 'header':
        return '全画面ヘッダ', 'レポートヘッダ'
    if s[1] in ('id', 'patientRef', 'status', 'verified', 'createdAt', 'updatedAt'):
        return 'サイドメニュー／システム', 'レポート管理'
    if s[1].startswith('history'):
        return 'サイドメニュー／システム', 'レポート登録履歴'
    sec, sub = s[1].replace('[]', ''), s[2] if len(s) > 2 else ''
    sub0 = sub.replace('[]', '')
    if sec == 'cathRecord':
        g = {'exam': '検査情報', 'doctors': '主治医・術者・紹介医', 'hemo': 'Hemodynamics', 'prognosis': '転帰および予後など', 'other': 'その他',
             'body': '検査値・危険因子（身体）', 'risk': '検査値・危険因子（危険因子）', 'pciSummary': 'PCIサマリー/連絡事項', 'futurePlan': '今後の方針', 'comment': 'Comment'}.get(sub0)
        if sub0 == 'labs':
            g = {'admission': '入院時(カテ時)／検査値', 'hbs': '入院時(カテ時)／HBs抗原', 'hcv': '入院時(カテ時)／HCV抗体', 'cbc': '入院時(カテ時)／入院時血算',
                 'endocrine': '入院時(カテ時)／甲状腺・副腎系/検尿', 'discharge': '退院時(カテ時)', 'dischargeDate': '退院時(カテ時)', 'bloodGas': '血ガス/AQT', 'legacy': '旧項目'}[s[3]]
        return 'カテ記録', g
    if sec == 'cagLvg':
        return 'CAG/LVG', {'approach': 'カテーテル／Approach', 'catheters': 'カテーテル／Catheter', 'cag': 'CAGタブ', 'lvg': 'LVGタブ'}[sub0]
    if sec == 'pci':
        if sub0 == 'lesions':
            k = s[3]
            g = ('Device' if k == 'device' else 'Bif/CTO' if k in ('bif', 'cto') else 'Complication' if k == 'comp' else '基本（病変一覧）' if k == 'summary'
                 else '検索用（ICT/IVT）' if k == 'ict' else 'J-PCI（PCI病変情報）' if k == 'success' else '病変形態' if k not in ('target', 'targetSub') else '全タブ共通（Target）')
            return 'PCI', g + '　※病変×5'
        return 'PCI', {'basic': '基本', 'ctoScore': 'Bif/CTO', 'patientComp': 'Complication', 'patientTreat': 'Complication', 'specificProcedure': 'Complication',
                       'risk': '出血・血栓リスク', 'ami': 'AMI'}.get(sub0) or ('J-PCI／' + {'bg': '患者背景', 'pre': '術前検査・投薬', 'post': '術後情報', 'info': 'PCI基本情報', 'discharge': '退院時情報'}[s[3]])
    if sec == 'pressureIvus':
        return 'Pressure/IVUS', 'Pressure Wire　※3列' if sub0 == 'pressure' else 'Lesion（IVUS）　※Lesion1〜4'
    if sec == 'pcps':
        return 'PCPS', 'PCPS詳細' if sub0 == 'detail' else 'PCPS'
    if sec == 'conference':
        g = {'prevPci': 'Previous PCI', 'scinti': 'Scintigram', 'mdct': 'MDCT', 'ucg': 'UCG', 'treadmill': 'Treadmill/処方', 'clinical': '臨床診断/感染症',
             'history': '既往歴/経過', 'dischargeRx': '退院時処方', 'notPerformed': '検査未実施フラグ'}.get(sub0, '基本・血行動態・危険因子')
        return 'カンファレンス', g
    if sec == 'mace':
        return 'MACE', 'MACE 1〜5　※5タブ'
    if sec == 'images':
        return '画像', '画像（複数）'
    if sec == 'restudy':
        return 'Restudy', 'Restudy'
    return sec, ''

def group_patient(k):
    if k in ('emergency', 'insurance'):
        return '緊急連絡先・保険'
    if k in ('allergy',):
        return 'アレルギー'
    if k == 'infection':
        return '感染症'
    if k in ('primaryDoctor', 'ward', 'referral', 'dnar'):
        return '主治医・紹介元'
    if k in ('pastHistory', 'familyHistory', 'medicationNote', 'notes'):
        return '既往歴・家族歴・内服'
    if k.startswith('admissions'):
        return '病歴総括（入院歴）'
    if k in ('id', 'createdAt', 'updatedAt'):
        return 'システム'
    return '基本情報'

# ------------------------------------------------------------------ 定数ベースのラベル
LAB = {
    'labs.admission': labdefs('LAB_CHEM_1', 'LAB_CHEM_2', 'LAB_CHEM_3'), 'labs.cbc': labdefs('LAB_CBC'), 'labs.endocrine': labdefs('LAB_ENDO'),
    'labs.discharge': labdefs('LAB_DISCHARGE'), 'labs.bloodGas': labdefs('LAB_GAS'), 'labs.legacy': labdefs('LAB_LEGACY'),
}
CTX = [  # (親パス末尾, ラベル辞書)
    ('exam.flags', kl('EXAM_FLAGS_LEFT', 'EXAM_FLAGS_RIGHT')), ('exam.purposes', kl('PURPOSES')),
    ('hemo.values', kl('HEMO_VALUES_RIGHT', 'HEMO_VALVE', 'HEMO_SHUNT')), ('lvg.wallMotion', kl('LV_SEGMENTS')),
    ('morph', kl('MORPH_YN', 'MORPH_YN2')), ('summary.tech', kl('PCI_TECH')), ('patientComp', kl('COMP_PATIENT')), ('patientTreat', kl('TREAT_PATIENT')),
    ('comp', {k: v for g in C['COMP_LESION'] for k, v in g['items']}),
    ('pre.imagingItems', kl('PREOP_IMAGING')), ('pre.apItems', kl('ANTIPLATELET')), ('pre.acItems', kl('ANTICOAG')), ('pre.legacy', kl('ANTICOAG_LEGACY')),
    ('post.antithrombotic', kl('POST_ANTITHROMBOTIC')), ('post.lipid', kl('POST_LIPID')), ('info.compItems', kl('JPCI_COMP')),
    ('info.mcsItems', kl('MCS_ITEMS')), ('info.mcsTiming', {k: v + ' タイミング' for k, v in kl('MCS_ITEMS').items()}), ('info.imagingItems', kl('IMAGING_ITEMS')),
    ('jpci.bg', kl('JPCI_BG_UMU_LEFT', 'JPCI_BG_24H')), ('risk.hbrMajor', kl('HBR_MAJOR')), ('risk.hbrMinor', kl('HBR_MINOR')),
    ('risk.credo', {r[0]: f'{r[1]}（{r[2]}点）' for r in C['CREDO_ITEMS']}), ('risk.st', kl('ST_RISK')),
    ('metrics', kl('PRESSURE_METRICS')), ('qca', kl('QCA_METRICS')), ('notPerformed', {k: f'検査未実施（{v}）' for k, v in kl('CONF_TABS').items()}),
]

def ctx_label(path):
    p = re.sub(r'\.\d+', '', path).replace('[]', '')
    s = p.split('.')
    parent, key = '.'.join(s[:-1]), s[-1]
    for suffix, table in LAB.items():
        if parent.endswith(suffix) and key in table:
            return table[key][0], table[key][1], table[key][2]
    for suffix, table in CTX:
        if parent.endswith(suffix) and key in table:
            return table[key], None, None
    # 3値・日時・カテーテル・セグメント・IVUS
    if len(s) >= 3 and s[-3] == 'pressures':
        return f'{s[-2].replace("AoPre", "Ao pre")} {TRIPLE[key]}', 'mmHg', None
    if s[-2] in STEPS and key in DT:
        return f'{STEPS[s[-2]]} {DT[key]}', None, None
    if len(s) >= 3 and s[-3] == 'catheters':
        slot = kl('CATHETER_SLOTS')[s[-2]]
        return f'{slot} ' + {'shape': '形状', 'size': 'サイズ', 'label': '名称（任意項目）'}[key], None, None
    if len(s) >= 3 and s[-3] == 'segments':
        f = {'size': 'Large/Small/Absent', 'calc': 'Calcification', 'stenosis': '狭窄度'}.get(key) or kl('SEG_FLAGS').get(key, key)
        return f'{SEG[s[-2]]} {f}', None, None
    if len(s) >= 3 and s[-3] in ('pre', 'post') and s[-2] in kl('IVUS_METRICS'):
        return f'{s[-3].capitalize()} {kl("IVUS_METRICS")[s[-2]]}（{kl("IVUS_POS")[key]}）', None, None
    return None, None, None

# ------------------------------------------------------------------ JSX 照合
def jsx_for(path, scr):
    norm = re.sub(r'\[\]', '.0', path)
    hits = [j for j in jsx if j['re'].search(norm)]
    if not hits:
        return None
    # 同じ画面フォルダのものを優先、パスが長い（具体的な）ものを優先
    folder = {'カテ記録': 'CathRecord', 'CAG/LVG': 'CagLvg', 'PCI': 'Pci', 'Pressure/IVUS': 'PressureIvus', 'カンファレンス': 'Conference', '画像': 'ImagesScreen',
              'PCPS': 'PcpsScreen', 'MACE': 'MaceScreen', 'Restudy': 'RestudyScreen', '患者情報入力': 'PatientInfo', '全画面ヘッダ': 'PatientHeader',
              '全画面ヘッダ／患者情報入力': 'PatientInfo'}.get(scr, '')
    spec = lambda j: sum(1 for seg in j['path'].lstrip('/').split('.') if '${' not in seg)
    hits.sort(key=lambda j: (bool(folder) and folder not in j['file'], -spec(j), clean_label(j['label']) is None))
    return hits

def clean_label(l):
    if not l:
        return None
    if l.startswith('{'):
        inner = l[1:-1].strip()
        if not inner.startswith('<'):
            return None
        l = inner
    if l.startswith('<') or '{' in l:
        t = re.sub(r'<[^>]+>', ' ', l)
        t = re.sub(r'\{[^}]*\}', '', t)
        t = re.sub(r'\s+', ' ', t).strip()
        return t or None
    return l

def options_text(expr):
    if not expr:
        return ''
    m = re.fullmatch(r'O\.(\w+)', expr.strip()) or re.fullmatch(r'(\w+_OPTS|\w+)', expr.strip())
    if m and m.group(1) in C:
        v = C[m.group(1)]
        if v and isinstance(v[0], dict):
            return ' / '.join(o['label'] for o in v)
        if v and isinstance(v[0], list):
            return ' / '.join(str(x[1]) for x in v)
        if v and isinstance(v[0], dict) is False and isinstance(v[0], str):
            return ' / '.join(v)
    lits = re.findall(r"'([^']*)'", expr)
    if lits and not expr.strip().startswith('names') and 'masters' not in expr:
        pairs = re.findall(r"\{\s*value:\s*'([^']*)',\s*label:\s*'([^']*)'\s*\}", expr)
        return ' / '.join(p[1] for p in pairs) if pairs else ' / '.join(lits)
    if 'masters.doctors' in expr or expr.strip() == 'docs':
        return '（マスタ：術者・医師）'
    if 'masters.hospitals' in expr:
        return '（マスタ：紹介病院）'
    if 'names(' in expr or 'devNames' in expr:
        return '（マスタ：デバイス）'
    if 'TARGET_LIST' in expr or 'CAG_SEGMENTS' in expr:
        return '（CAGセグメント #1〜#15 等）'
    return ''

SHARED = {
    'cathRecord.exam.fluoroTime': 'PCI J-PCI と共通', 'cathRecord.exam.contrast.agent': 'PCI J-PCI と共通', 'cathRecord.exam.contrast.volume': 'PCI J-PCI と共通',
    'cathRecord.risk.DM': 'J-PCI・カンファレンスと共通', 'cathRecord.risk.HT': 'J-PCI・カンファレンスと共通', 'cathRecord.risk.HL': 'J-PCI・カンファレンスと共通',
    'cathRecord.risk.HD': 'J-PCI・カンファレンスと共通', 'cathRecord.risk.CAPD': 'カンファレンスと共通', 'cathRecord.risk.family': 'カンファレンスと共通',
    'cathRecord.risk.smoking': 'カンファレンスと共通', 'cathRecord.risk.smokingPerDay': 'カンファレンスと共通', 'cathRecord.risk.DMtreatment': 'カンファレンスと共通',
    'cathRecord.labs.cbc.Hb': 'J-PCI と共通', 'cathRecord.labs.admission.Cr': 'J-PCI と共通',
    'cathRecord.body.height': 'カンファレンスと共通（BSA・BMI算出）', 'cathRecord.body.weight': 'カンファレンスと共通（BSA・BMI算出）',
    'cathRecord.hemo.': 'カンファレンスと共通', 'cathRecord.prognosis.deathDate': 'カンファレンスと共通', 'cathRecord.prognosis.confirmDate': 'カンファレンスと共通',
    'cathRecord.prognosis.confirmer': 'カンファレンスと共通', 'cathRecord.prognosis.comment': 'カンファレンスと共通',
    'cathRecord.labs.hbs.': 'カンファレンス（臨床診断/感染症）と共通', 'cathRecord.labs.hcv.': 'カンファレンス（臨床診断/感染症）と共通',
    'cagLvg.cag.syntax': 'PCI 基本と共通', 'cagLvg.cag.euro': 'PCI 基本と共通', 'cagLvg.cag.japan': 'PCI 基本と共通',
    'cagLvg.lvg.values.LVEDV': 'カンファレンスと共通', 'cagLvg.lvg.values.LVESV': 'カンファレンスと共通', 'cagLvg.lvg.values.LVSV': 'カンファレンスと共通',
    'cagLvg.lvg.values.EF': 'カンファレンスと共通', 'cagLvg.lvg.values.LVEDVI': 'カンファレンスと共通', 'cagLvg.lvg.values.LVESVI': 'カンファレンスと共通', 'cagLvg.lvg.values.LVSVI': 'カンファレンスと共通',
    'pci.jpci.pre.': 'PCI 基本（術前検査・投薬）と共通', 'pci.lesions[].target': 'PCI全タブ共通・画像の対象病変候補',
    'pci.ami.': 'Door to balloon 等を自動算出（基本・J-PCI・集計で参照）', 'pressureIvus.pressure[].qca.': 'PCI 病変形態の「取得」で参照',
    'patient.infection.': 'カンファレンス（臨床診断/感染症）と共通', 'patient.pastHistory': 'カンファレンス（既往歴）と共通',
    'patient.admissions[]': 'カンファレンス（病歴総括）で参照', 'report.header.summary': 'カンファレンス画面ヘッダで入力・一覧に表示',
    'report.header.submitted': 'カンファレンス画面ヘッダで入力・一覧に表示', 'report.header.secretaryChecked': 'カテ記録画面ヘッダで入力・一覧に表示',
    'report.header.accessionNo': 'カテ記録画面ヘッダで入力', 'cathRecord.exam.purposes.followUp': '一覧の FollowUp 列に表示',
}
COND = {
    'followUpReason': 'Follow-up チェック時に入力可', 'cancerName': '担癌患者 チェック時に入力可', 'aorticDiseaseType': '大動脈疾患 チェック時に入力可',
    'other1Text': 'その他1 チェック時に入力可', 'other2Text': 'その他2 チェック時に入力可', 'collaterals[]': '「なし」チェック時は入力不可',
    'stagedText': 'Staged PCI チェック時に入力可',
}
REQUIRED = {'patient.patientId', 'patient.name', 'report.header.studyDate'}
CALC = {
    'cagLvg.lvg.values.LVSV': 'LVEDV−LVESV（算出ボタン）', 'cagLvg.lvg.values.EF': 'SV/LVEDV（算出ボタン）', 'cagLvg.lvg.values.LVEDVI': '÷BSA（算出ボタン）',
    'cagLvg.lvg.values.LVESVI': '÷BSA（算出ボタン）', 'cagLvg.lvg.values.LVSVI': '÷BSA（算出ボタン）', 'cagLvg.lvg.values.CO': 'SV×HR（算出ボタン）', 'cagLvg.lvg.values.CI': 'CO÷BSA（算出ボタン）',
    '.plaqueCSA.': '血管CSA−内腔CSA（算出ボタン）', '.plaqueBurden.': 'プラークCSA÷血管CSA（算出ボタン）', '.eccentricity.': '(最大−最小)÷最大プラーク厚（算出ボタン）',
    'device.final.': 'Device1〜10から算出可', 'cag.lesions.': '所見から算出可', '.pre.ref': 'Pressure Wire QCA から取得可', '.pre.pct': 'Pressure Wire QCA から取得可', '.pre.mld': 'Pressure Wire QCA から取得可',
}

def find(d, path):
    for k in sorted(d, key=len, reverse=True):
        if k in path:
            return d[k]
    return ''

# ------------------------------------------------------------------ Excel 出力
def build_xlsx(rows):
    import datetime
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo

    out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / 'docs/field_list.xlsx')
    F = 'Arial'
    thin = Side(style='thin', color='B8C4C0')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    head_fill = PatternFill('solid', fgColor='3F5560')
    head_font = Font(name=F, bold=True, color='FFFFFF', size=10)
    body = Font(name=F, size=10)
    wrap = Alignment(vertical='top', wrap_text=True)
    SCREEN_ORDER = ['全画面ヘッダ', '全画面ヘッダ／患者情報入力', '患者情報入力', 'サイドメニュー／システム', 'カテ記録', 'CAG/LVG', 'PCI', 'Pressure/IVUS', 'PCPS',
                    'カンファレンス', 'MACE', '画像', 'Restudy', 'マスタ編集']
    TINT = {'全画面ヘッダ': 'F4EFE0', '全画面ヘッダ／患者情報入力': 'F4EFE0', '患者情報入力': 'F4EFE0', 'サイドメニュー／システム': 'EEF0F2', 'カテ記録': 'E3F2E5',
            'CAG/LVG': 'E6F0FA', 'PCI': 'FDF1E2', 'Pressure/IVUS': 'F3E8F7', 'PCPS': 'EEF0F2', 'カンファレンス': 'E8F4F3', 'MACE': 'FBEAEA', '画像': 'EEF0F2',
            'Restudy': 'EEF0F2', 'マスタ編集': 'E8EEF3'}
    rows = sorted(rows, key=lambda r: SCREEN_ORDER.index(r[0]) if r[0] in SCREEN_ORDER else 99)

    wb = Workbook()
    # ---------------- 項目一覧
    ws = wb.active
    ws.title = '項目一覧'
    headers = ['No', '画面', '区分・タブ', '項目名', '項目パス（DB）', 'データ型', '入力形式', '選択肢・入力候補', '単位', '繰返し', '展開数', '必須', '備考（共有・入力条件・算出・基準値）']
    widths = [6, 18, 30, 30, 46, 9, 22, 40, 9, 18, 8, 6, 48]
    ws.append(headers)
    for i, r in enumerate(rows, 1):
        ws.append([i] + r)
    n = len(rows) + 1
    for c, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(c)].width = w
    for cell in ws[1]:
        cell.font, cell.fill, cell.border = head_font, head_fill, border
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[1].height = 30
    for row in ws.iter_rows(min_row=2, max_row=n):
        fill = PatternFill('solid', fgColor=TINT.get(row[1].value, 'FFFFFF'))
        for cell in row:
            cell.font, cell.border, cell.alignment = body, border, wrap
        for c in (1, 2):
            row[c - 1].fill = fill
        row[0].alignment = Alignment(horizontal='right', vertical='top')
        for c in (6, 11, 12):
            row[c - 1].alignment = Alignment(horizontal='center', vertical='top')
        row[4].font = Font(name='Consolas', size=9, color='33515C')
        if row[11].value:
            row[11].font = Font(name=F, size=10, bold=True, color='C0392B')
    tab = Table(displayName='FieldList', ref=f'A1:M{n}')
    tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight1', showRowStripes=False)
    ws.add_table(tab)
    ws.freeze_panes = 'E2'

    # ---------------- 画面別集計（数式）
    ss = wb.create_sheet('画面別集計', 0)
    ss['A1'] = '心カテーテルレポート 全入力項目一覧'
    ss['A1'].font = Font(name=F, size=16, bold=True, color='2C3E45')
    ss['A2'] = f'生成日: {datetime.date.today():%Y/%m/%d}　出典: frontend/src/model/defaults.ts（データ構造）・画面ソース（*.tsx）・constants/options.ts'
    ss['A2'].font = Font(name=F, size=9, color='6B7A7E')
    hdr = ['画面', '項目数（定義）', '展開後項目数', 'うち必須', '共有・連携項目']
    for c, h in enumerate(hdr, 1):
        cell = ss.cell(row=4, column=c, value=h)
        cell.font, cell.fill, cell.border = head_font, head_fill, border
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    screens = [s for s in SCREEN_ORDER if any(r[0] == s for r in rows)]
    for i, sname in enumerate(screens):
        r = 5 + i
        ss.cell(row=r, column=1, value=sname)
        ss.cell(row=r, column=2, value=f"=COUNTIF(項目一覧!$B$2:$B${n},A{r})")
        ss.cell(row=r, column=3, value=f"=SUMIF(項目一覧!$B$2:$B${n},A{r},項目一覧!$K$2:$K${n})")
        ss.cell(row=r, column=4, value=f'=COUNTIFS(項目一覧!$B$2:$B${n},A{r},項目一覧!$L$2:$L${n},"○")')
        ss.cell(row=r, column=5, value=f'=COUNTIFS(項目一覧!$B$2:$B${n},A{r},項目一覧!$M$2:$M${n},"*【編集】*")+COUNTIFS(項目一覧!$B$2:$B${n},A{r},項目一覧!$M$2:$M${n},"*共通*")')
        for c in range(1, 6):
            cell = ss.cell(row=r, column=c)
            cell.font, cell.border = body, border
            if c > 1:
                cell.number_format = '#,##0'
        ss.cell(row=r, column=1).fill = PatternFill('solid', fgColor=TINT.get(sname, 'FFFFFF'))
    tr = 5 + len(screens)
    ss.cell(row=tr, column=1, value='合計')
    for c in range(2, 6):
        col = get_column_letter(c)
        ss.cell(row=tr, column=c, value=f'=SUM({col}5:{col}{tr - 1})').number_format = '#,##0'
    for c in range(1, 6):
        cell = ss.cell(row=tr, column=c)
        cell.font, cell.border = Font(name=F, size=10, bold=True), border
        cell.fill = PatternFill('solid', fgColor='E4EBE7')
    for c, w in enumerate([30, 16, 16, 12, 16], 1):
        ss.column_dimensions[get_column_letter(c)].width = w

    notes = [
        ('凡例', ''),
        ('項目数（定義）', '項目パス単位の件数。PCI 病変×5 や Device×10 などの繰返しは1件として数えます。'),
        ('展開後項目数', '繰返しを展開した実際の入力欄数（展開数の合計）。画像・マスタなど件数可変のものは1として計算。'),
        ('項目パス（DB）', 'MongoDB に保存されるパス。patient.* は patients コレクション、report.* は cath_reports コレクション、masters.* は masters コレクション。[] は配列要素。'),
        ('データ型', 'string（未入力は空文字。数値・日付も文字列で保存し、表示・計算時に変換）/ boolean。'),
        ('備考', '【編集】の画面でのみ入力でき、【参照のみ】の画面では淡い青・点線枠の参照表示（編集不可、編集画面へのリンク付き）。「共通」は同一画面内の複数タブで共有。「算出」はボタンまたは自動計算。基準値は範囲外をピンク表示。'),
        ('必須', '保存時に必須チェックを行う項目（患者ID・氏名・施行日）。'),
    ]
    base = tr + 2
    for i, (k, v) in enumerate(notes):
        a = ss.cell(row=base + i, column=1, value=k)
        b = ss.cell(row=base + i, column=2, value=v)
        a.font = Font(name=F, size=10, bold=(i == 0 or True), color='2C3E45')
        b.font = Font(name=F, size=10)
        ss.merge_cells(start_row=base + i, start_column=2, end_row=base + i, end_column=5)
        b.alignment = Alignment(wrap_text=True, vertical='top')
        ss.row_dimensions[base + i].height = 30 if v else 18

    # ---------------- 選択肢マスタ
    os_ = wb.create_sheet('選択肢一覧')
    os_.append(['区分', '選択肢'])
    OPT_SETS = [('−/+/不明', 'PM_OPTS'), ('−/+', 'PM2_OPTS'), ('Yes/No', 'YN_OPTS'), ('有/無/不明', 'UMU_OPTS'), ('有/無', 'UM_OPTS'), ('待機/緊急', 'URGENCY_OPTS'),
                ('喫煙', 'SMOKING_OPTS'), ('喫煙（J-PCI）', 'JPCI_SMOKING_OPTS'), ('補助循環タイミング', 'TIMING_OPTS'), ('狭窄度', 'STENOSIS'), ('血管サイズ', 'SEG_SIZES'),
                ('Rentrop', 'RENTROP'), ('グラフト通行状態', 'GRAFT_PATENCY'), ('壁運動', 'WALL_MOTION'), ('Sellers', 'SELLERS'), ('病変Type', 'LESION_TYPES'),
                ('TIMI', 'TIMI'), ('PCI結果', 'PCI_RESULTS'), ('デバイス種別', 'DEVICE_CATEGORIES'), ('分岐部ステント', 'BIF_STENTS'), ('CTO Access', 'CTO_ACCESS'),
                ('GW通過法', 'GW_METHOD'), ('サポート', 'SUPPORTS'), ('検査項目', 'EXAM_ITEMS'), ('疾病', 'DISEASES'), ('アプローチ', 'APPROACHES'),
                ('造影剤', 'CONTRAST_AGENTS'), ('カテーテル形状', 'CATHETER_SHAPES'), ('シース', 'SHEATH_NAMES'), ('Pressure 病変区分', 'PRESSURE_PHASE'),
                ('充血薬剤', 'HYPEREMIC_DRUGS'), ('Dominancy', 'DOMINANCY'), ('初回心電図', 'FIRST_ECG'), ('画像種別', 'IMAGE_CATEGORIES'), ('撮影方向', 'IMAGE_VIEWS'),
                ('NYHA', 'NYHA'), ('CCS', 'CCS'), ('シンチ種類', 'SCINTI_TYPES'), ('CAD-RADS', 'CAD_RADS'), ('負荷プロトコル', 'TREADMILL_PROTOCOLS'),
                ('負荷判定', 'TREADMILL_RESULTS'), ('用法', 'DRUG_USAGE'), ('1ヶ月以内の症状', 'SYMPTOMS_1M'), ('入院時診断名(J-PCI)', 'JPCI_DX')]
    for k, name in OPT_SETS:
        if name in C:
            v = C[name]
            txt = ' / '.join(o['label'] if isinstance(o, dict) else str(o) for o in v)
            os_.append([k, txt])
    os_.column_dimensions['A'].width = 24
    os_.column_dimensions['B'].width = 110
    for i, row in enumerate(os_.iter_rows(), 1):
        for cell in row:
            cell.border = border
            cell.font = head_font if i == 1 else body
            if i == 1:
                cell.fill = head_fill
            else:
                cell.alignment = wrap
    os_.freeze_panes = 'A2'

    for sh in wb.worksheets:
        sh.sheet_view.zoomScale = 90
    ws.auto_filter  # テーブルにフィルタあり
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = '1:1'
    wb.save(out)
    print('written', out)


# ------------------------------------------------------------------ 主画面（編集可）定義: frontend/src/model/ownership.ts
SCREEN_JP = {'patient': '患者情報入力', 'cathRecord': 'カテ記録', 'cagLvg': 'CAG/LVG', 'pci': 'PCI', 'conference': 'カンファレンス'}
OWN = [(m.group(1), [SCREEN_JP.get(x, x) for x in re.findall(r"'(\w+)'", m.group(2))], m.group(3))
       for m in re.finditer(r"prefix: '([^']+)', owner: \[([^\]]*)\], refs: '([^']*)'", (SRC / 'model/ownership.ts').read_text(encoding='utf-8'))]


def ownership_note(path):
    for prefix, owners, refs in OWN:
        if path == prefix or path.startswith(prefix + '.'):
            return f'【編集】{"・".join(owners)}　【参照のみ】{refs}'
    return ''


# ------------------------------------------------------------------ 行生成
rows = []
for lf in LEAVES:
    path, typ = lf['path'], lf['type']
    scr, grp = screen(path)
    hits = jsx_for(path, scr) or []
    j = hits[0] if hits else None
    lab_c, unit_c, rng = ctx_label(path)
    label = None
    for h in hits:
        label = clean_label(h['label'])
        if label:
            break
    if label and j and j['comp'] == 'TripleF':
        label = f'{label} {TRIPLE[path.split(".")[-1]]}'
    if label and j and j['comp'] == 'DateTimeF':
        label = f'{label} {DT[path.split(".")[-1]]}'
    label = lab_c or label
    label = manual(path) or label
    if not label:
        for h in hits[:1]:
            if h.get('ph'):
                label = h['ph']
    label = label or path.split('.')[-1]
    comp = COMP.get(j['comp'], '') if j else ''
    if comp.startswith('3値'):
        comp = '数値入力（3値の1つ）'
    if comp == '日付＋時刻':
        comp = '日付' if path.endswith('.date') else '時刻'
    if '.labs.' in path and not re.search(r'\.(hbs|hcv)\.', path) and not path.endswith('dischargeDate'):
        comp = '数値入力（検査値・基準外はピンク表示）'
    if re.search(r'pressureIvus\.lesions\[\]\.(pre|post)\.', path):
        comp = '数値入力'
    if re.search(r'lesions\[\]\.(comp|morph)\.', path) or path.endswith('desHybrid') or path.endswith('desBmsHybrid') or path.endswith('parallelWire'):
        comp, j = 'ラジオボタン', None
    if not comp:
        comp = 'チェックボックス' if typ == 'boolean' else ('自動設定' if re.search(r'(\.id|At|patientRef|history.*|mimeType|fileName|dataUrl)$', path) else '文字入力')
    if path.endswith('.dataUrl'):
        comp = 'ファイル選択（画像アップロード）'
    if path in ('report.status', 'report.verified'):
        comp = 'ボタン切替（サイドメニュー）'
    if path == 'report.header.registrant':
        comp = 'プルダウン（トップバー）'
    opts = options_text(j['options']) if j else ''
    if comp == 'ラジオボタン' and re.search(r'lesions\[\]\.(comp|morph)\.|Hybrid$|parallelWire$', path):
        opts = 'Yes / No'
    if j and j['comp'] in ('CellRadio',) and 'stenosis' in path:
        opts = ' / '.join(C['STENOSIS'])
    if j and j['comp'] in ('CellRadio',) and path.endswith('.size'):
        opts = ' / '.join(C['SEG_SIZES'])
    if path.endswith('wallMotion.1') or re.search(r'wallMotion\.\d$', path):
        opts = ' / '.join(o['label'] for o in C['WALL_MOTION'])
    unit = unit_c or ''
    if not unit and j and j['unit'] and not j['unit'].startswith('<'):
        unit = j['unit'].strip('"')
    rep, expand = '', 1
    for a in re.findall(r'(\w+)\[\]', path):
        key = path[: path.index(a + '[]') + len(a)]
        n = ARRLEN.get(key)
        rep += f'{a}×{n if n else "可変"} '
        expand *= n or 1
    note = '　'.join(x for x in [COND.get(path.split('.')[-1]) or find({k: v for k, v in COND.items() if '[]' in k}, path),
                                 ownership_note(path) or find(SHARED, path.replace('report.', '')),
                                 find(CALC, path), rng or ''] if x)
    rows.append([scr, grp, label, path, 'boolean' if typ == 'boolean' else 'string', comp, opts, unit, rep.strip(), expand, '○' if path in REQUIRED else '', note])

# マスタ（masters コレクション）
rows += [
    ['マスタ編集', '術者・医師', '術者・医師名', 'masters.doctors[]', 'string', '文字入力（一覧編集）', '', '', 'doctors×可変', 1, '', '術者・主治医等の入力候補'],
    ['マスタ編集', '紹介病院', '紹介病院名', 'masters.hospitals[]', 'string', '文字入力（一覧編集）', '', '', 'hospitals×可変', 1, '', '紹介病院の入力候補'],
    ['マスタ編集', 'デバイス', 'デバイス種別', 'masters.devices[].category', 'string', '文字入力（一覧編集）', '', '', 'devices×可変', 1, '', 'PCI Device・GW・マイクロ等の入力候補'],
    ['マスタ編集', 'デバイス', 'デバイス名称', 'masters.devices[].name', 'string', '文字入力（一覧編集）', '', '', 'devices×可変', 1, '', ''],
]
json.dump(rows, open('/tmp/field_rows.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('rows', len(rows))
build_xlsx(rows)
