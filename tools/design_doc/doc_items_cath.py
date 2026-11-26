"""カテ記録 画面項目一覧"""
from extra_common import G, e, table, build_doc, RELATED
from items_common import ITEM_CSS, V, L, SHARE, CALC, REP, REF, Counter, items, labs, shot, legend, kind_legend, wrap

C = Counter('CR')
R = 'report.cathRecord'


def p_overview():
    return ('<h1>1. 画面の概要</h1>'
            '<p class="lead">カテ記録は、1回のカテーテル検査・治療の基本情報（検査の目的・術者・血行動態・検査値・危険因子・転帰）を記録する画面です。'
            '保存先は <span class="code">report.cathRecord</span>（共通ヘッダーは <span class="code">report.header</span>・<span class="code">patient</span>）です。</p>' +
            shot('06_cath_labs_risk.png', 'カテ記録（入院時：検査値・危険因子）') +
            '<h2>画面の構成</h2>' +
            table(['領域', 'パネル', 'データ', '内容'], [
                ('上部', '患者属性（共通ヘッダー）', 'report.header／patient', '施行日・ID・Cine.No・PCI.No・氏名・性別・生年月日・年齢・フリガナ。秘書入力確認・AccessionNo.'),
                ('左', '検査情報', R + '.exam', '待機/緊急・目的・検査項目・疾病・診断・治療方針・フラグ・担癌・大動脈疾患・アプローチ・シース・造影剤・透視時間・総線量'),
                ('左', '主治医・術者・紹介医', R + '.doctors', '主治医・外来主治医・術者3名・助手3名・紹介病院・紹介医'),
                ('左', 'Hemodynamics', R + '.hemo', '各部位の圧（収縮期/拡張期/平均）・HR・CO・CI・SV・SI・dp/dt・弁口・シャント'),
                ('左', '転帰および予後など', R + '.prognosis', '死亡日・確認日・確認者・予後コメント・転帰日・MACE と当院経過・AngioFU 対象外理由'),
                ('左', 'その他', R + '.other', 'Study1・2・メモ'),
                ('右', '検査値・危険因子（タブ）', R + '.labs／risk／body', '入院時（化学・血算・内分泌/検尿）・退院時・血ガス/AQT・旧項目、身体所見、感染症、危険因子'),
                ('右', 'PCIサマリー・今後の方針・Comment', R, '文章（Comment は過去レポートからコピー可）'),
            ], widths=['12mm', '40mm', '40mm', None]) +
            '<h2>入力形式と記号</h2>' + kind_legend() + legend())


def p_header():
    return ('<h1>2. 共通ヘッダー</h1><p class="lead">全画面の上部に表示されます。カテ記録・患者情報の画面では編集でき、他の画面では参照のみです。</p>' +
            items(C, [
                ('患者属性', '', [
                    ('施行日', 'report.header.studyDate', 'D', '', '年齢計算・前回データの検索に使用'),
                    ('ID', 'patient.patientId', 'T', '', '必須'),
                    ('Cine.No', 'report.header.cineNo', 'T'),
                    ('PCI.No', 'report.header.pciNo', 'T'),
                    ('氏名', 'patient.name', 'T', '', '必須'),
                    ('性別', 'patient.sex', 'R', 'M／F'),
                    ('生年月日', 'patient.birthDate', 'D'),
                    ('年齢', '（計算）', 'K', '歳', CALC + '施行日時点の満年齢'),
                    ('フリガナ', 'patient.kana', 'T'),
                ]),
                ('カテ記録のヘッダー', 'report.header', [
                    ('秘書入力確認チェック', 'secretaryChecked', 'C', '', '秘書が入力内容を確認した印'),
                    ('AccessionNo.', 'accessionNo', 'T', '', 'オーダー番号'),
                ]),
            ]))


def p_exam():
    return ('<h1>3. 検査情報</h1>' + items(C, [
        ('検査情報', R + '.exam', [
            ('待機／緊急', 'urgency', 'R', V('URGENCY_OPTS'), SHARE + 'J-PCI の PCI ステータスと同じ区分'),
            ('総カテ回数', 'totalCathCount', 'N', '回'),
            ('目的', 'purposes.{CAG,PCI,SG,EVT}', 'C', V('PURPOSES'), '複数選択'),
            ('目的：Follow-up', 'purposes.followUp', 'C'),
            ('Follow-up の理由', 'followUpReason', 'T', '', 'Follow-up をチェックした時のみ入力可'),
            ('目的：その他1・2', 'purposes.other1／other2', 'C'),
            ('その他1・2 の内容', 'other1Text／other2Text', 'T', '', 'チェックした時のみ入力可'),
            ('検査項目', 'examItems', 'TL', V('EXAM_ITEMS'), '例：CAG,LVG,PCI（カンマ区切り）'),
            ('疾病', 'disease', 'TL', V('DISEASES')),
            ('診断', 'diagnosis', 'T'),
            ('治療方針（冠動脈病変）', 'treatmentPolicy', 'A'),
            ('CCUホットライン', 'flags.ccuHotline', 'C'),
            ('ImpressiveCase', 'flags.impressiveCase', 'C'),
            ('施行フラグ', 'flags.{ptcra,pwIfr,pwRfr,achProvocation,cfrImr,ppg}', 'C', 'PTCRA／Pressurewire(iFR)／Pressurewire(RFR)／Ach provocation／CFR IMR／PPG', '6項目'),
            ('担癌患者', 'cancer', 'C'),
            ('癌の名称', 'cancerName', 'T', '', '担癌患者をチェックした時のみ'),
            ('大動脈疾患', 'aorticDisease', 'C'),
            ('大動脈疾患分類', 'aorticDiseaseType', 'TL', '胸部大動脈瘤／腹部大動脈瘤／大動脈解離 Stanford A／Stanford B／大動脈弁狭窄症／その他', '大動脈疾患をチェックした時のみ'),
            ('アプローチ', 'approach', 'TL', V('APPROACHES'), SHARE + 'CAG のカテーテル欄へ反映ボタンあり'),
            ('シース（名称）', 'sheath.name', 'TL', V('SHEATH_NAMES')),
            ('シース（サイズ）', 'sheath.size', 'TL', V('SHEATH_SIZES') + '（Fr）'),
            ('造影剤', 'contrast.agent', 'TL', V('CONTRAST_AGENTS'), SHARE + 'J-PCI タブでも編集'),
            ('造影剤量', 'contrast.volume', 'N', 'ml', SHARE + 'J-PCI'),
            ('透視時間', 'fluoroTime', 'N', '分', SHARE + 'J-PCI'),
            ('総線量', 'totalDose', 'N', 'mGy'),
            ('手技開始・終了', 'startTime／endTime', 'T', 'HH:MM（時刻）', '確定前の確認で必須'),
            ('手技時間', '（計算）', 'K', '分', CALC + '終了−開始。終了が開始より前なら日付をまたいだとみなす'),
        ]),
    ]))


def p_staff():
    return ('<h1>4. 術者・血行動態・転帰・その他</h1>' + items(C, [
        ('主治医・術者・紹介医', R + '.doctors', [
            ('主治医', 'attending', 'TL', '医師マスタ', '「マスタ編集」で医師マスタを編集'),
            ('外来主治医', 'outpatient', 'TL', '医師マスタ'),
            ('術者（1〜3）', 'operators[0..2]', 'TL', '医師マスタ', REP + '3名'),
            ('助手（1〜3）', 'assistants[0..2]', 'TL', '医師マスタ', REP + '3名'),
            ('紹介病院', 'referralHospital', 'TL', '病院マスタ'),
            ('紹介医', 'referralDoctor', 'T'),
        ]),
        ('Hemodynamics：圧（mmHg）', R + '.hemo.pressures', [
            (lab, f'{k}.{{s,d,m}}', 'P', 'mmHg', '') for k, lab in [('RA', 'RA'), ('RV', 'RV'), ('PA', 'PA'), ('PCW', 'PCW'), ('LV', 'LV'), ('LVpost', 'LVpost'), ('Ao', 'Ao'), ('AoPre', 'Ao pre')]
        ]),
        ('Hemodynamics：数値', R + '.hemo.values', [
            ('HR', 'HR', 'N', '/min', SHARE + 'LVG の CO・CI 算出に使用'), ('CO', 'CO', 'N', 'L/min'), ('CI', 'CI', 'N', 'L/min/m²'), ('SV', 'SV', 'N', 'ml'), ('SI', 'SI', 'N', 'ml/m²'), ('dp/dt', 'dpdt', 'N', 'mmHg/s'),
            ('MVG', 'MVG', 'N', 'mmHg（僧帽弁圧較差）'), ('MVA', 'MVA', 'N', 'cm²'), ('AVG', 'AVG', 'N', 'mmHg（大動脈弁圧較差）'), ('AVA', 'AVA', 'N', 'cm²'),
            ('L→R', 'LtoR', 'N', '%'), ('R→L', 'RtoL', 'N', '%'), ('Qp/Qs', 'QpQs', 'N', '比'), ('Rp/Rs', 'RpRs', 'N', '比'),
            ('数値取得', '－', 'B', '', 'ポリグラフ連携（未設定）'),
        ]),
        ('転帰および予後など', R + '.prognosis', [
            ('死亡日', 'deathDate', 'D'), ('確認日', 'confirmDate', 'D'), ('確認者', 'confirmer', 'TL', '医師マスタ'),
            ('予後コメント', 'comment', 'A'), ('転帰日', 'transferDate', 'D'),
            ('MACEと当院経過関係', 'maceRelation', 'TL', '当院通院中／紹介元通院／転院／死亡／不明'),
            ('AngioFU対象外理由', 'angioFuExclude', 'TL', '高齢／腎機能障害／本人希望せず／他院フォロー／死亡'),
            ('AngioFU対象外理由（2）', 'angioFuExclude2', 'T'),
        ]),
        ('その他', R + '.other', [('Study1', 'study1', 'T'), ('Study2', 'study2', 'T'), ('メモ', 'memo', 'T')]),
        ('合併症（全検査共通）', R + '.complications', [
            ('合併症の有無', 'status', 'R', V('UMU_OPTS'), '確定前の確認で必須'),
            ('合併症の内容', 'items.*', 'C', V('CATH_COMP'), '「有」のときに選択'),
            ('内容・対応', 'detail', 'T'),
        ]),
        ('文章', R, [
            ('PCIサマリー／連絡事項', 'pciSummary', 'A', '', '「PCIへ」ボタンで PCI 画面へ'),
            ('今後の方針', 'futurePlan', 'A'),
            ('Comment', 'comment', 'A', '', '過去レポートの Comment をコピー可'),
        ]),
    ]))


def p_labs():
    return ('<h1>5. 検査値・身体所見・危険因子</h1>'
            '<p class="lead">右側のタブ（入院時(カテ時)・退院時(カテ時)・血ガス/AQT・旧項目）で入力します。入院時はさらに「検査値・危険因子」「入院時血算」「甲状腺・副腎系/検尿」に分かれます。'
            '基準範囲のある項目は、範囲外の値をピンクで表示します。</p>' +
            labs(R + '.labs.admission', 'LAB_CHEM_1', '入院時：生化学（1列目）', C) +
            labs(R + '.labs.admission', 'LAB_CHEM_2', '入院時：心筋・糖・脂質（2列目）', C) +
            labs(R + '.labs.admission', 'LAB_CHEM_3', '入院時：脂肪酸・ケトン体ほか（3列目）', C) +
            items(C, [
                ('身体所見', R + '.body', [
                    ('体温（カテ日）', 'bodyTemp', 'N', '℃'), ('身長', 'height', 'N', 'cm', SHARE + 'BSA・BMI・LVG の Index 算出'), ('体重', 'weight', 'N', 'kg', SHARE),
                    ('BSA', '（計算）', 'K', 'm²', CALC + 'DuBois：0.007184×体重^0.425×身長^0.725'),
                    ('BMI', '（計算）', 'K', 'kg/m²', CALC + '体重÷身長(m)²'),
                ]),
                ('感染症', R + '.labs', [
                    ('HBs：検査日', 'hbs.date', 'D'), ('HBs抗原', 'hbs.hbsAg', 'TL', '(-)／(+)／(±)'), ('HBs抗原C（定量）', 'hbs.hbsAgC', 'N'),
                    ('HCV：検査日', 'hcv.date', 'D'), ('HCV抗体', 'hcv.hcvAb', 'TL', '(-)／(+)／(±)'), ('HCV抗体C（定量）', 'hcv.hcvAbC', 'N'),
                ]),
            ]) +
            labs(R + '.labs.cbc', 'LAB_CBC', '入院時血算・凝固', C) +
            labs(R + '.labs.endocrine', 'LAB_ENDO', '甲状腺・副腎系／検尿（入院カテ時）', C) +
            items(C, [('退院時（カテ時）', R + '.labs', [('採血日', 'dischargeDate', 'D')])]) +
            labs(R + '.labs.discharge', 'LAB_DISCHARGE', '退院時（カテ時）：検査値', C) +
            labs(R + '.labs.bloodGas', 'LAB_GAS', '血ガス／AQT', C) +
            labs(R + '.labs.legacy', 'LAB_LEGACY', '旧項目（過去データの参照用）', C) +
            items(C, [
                ('危険因子', R + '.risk', [
                    ('DM', 'DM', 'R', V('PM_OPTS'), SHARE + 'J-PCI の患者背景'),
                    ('DM の治療', 'DMtreatment', 'TL', '食事療法／内服／インスリン／GLP-1RA'),
                    ('HT', 'HT', 'R', V('PM_OPTS'), SHARE + 'J-PCI'),
                    ('HL', 'HL', 'R', V('PM_OPTS'), SHARE + 'J-PCI'),
                    ('HD（血液透析）', 'HD', 'R', V('PM2_OPTS'), SHARE + 'J-PCI'),
                    ('CAPD', 'CAPD', 'R', V('PM2_OPTS')),
                    ('家族歴', 'family', 'R', V('PM_OPTS')),
                    ('喫煙', 'smoking', 'R', V('SMOKING_OPTS'), 'J-PCI の喫煙（過去1年以内）は別項目'),
                    ('喫煙：開始年齢・本数・禁煙年齢', 'smokingStartAge／smokingPerDay／smokingQuitAge', 'N', '歳／本/日／歳'),
                    ('電子煙草', 'eSmoking', 'R', V('SMOKING_OPTS')),
                    ('電子煙草：開始年齢・本数・禁煙年齢', 'eSmokingStartAge／eSmokingPerDay／eSmokingQuitAge', 'N', '歳／本/日／歳'),
                ]),
                ('既往歴・併存症（全検査で記録）', R + '.risk', [
                    ('心筋梗塞の既往', 'priorMI', 'R', V('UMU_OPTS'), SHARE + 'J-PCI（参照）。旧データは J-PCI から移行'),
                    ('心不全の既往', 'priorHF', 'R', V('UMU_OPTS'), SHARE + 'J-PCI（参照）'),
                    ('PCI歴', 'pciHx', 'R', V('UMU_OPTS'), SHARE + 'J-PCI（参照）'),
                    ('CABG歴', 'cabgHx', 'R', V('UMU_OPTS'), SHARE + 'J-PCI（参照）'),
                    ('腎不全', 'renal', 'R', V('PM_OPTS'), SHARE + 'J-PCI（参照）'),
                    ('COPD', 'copd', 'R', V('PM_OPTS'), SHARE + 'J-PCI（参照）'),
                    ('AAA/PAD', 'pad', 'R', V('PM_OPTS'), SHARE + 'J-PCI（参照）'),
                ]),
                ('操作', '', [
                    ('前回からコピー', '－', 'B', '', '同じ患者の直前（施行日が同日以前）のカテ記録から 検査値・危険因子・身体所見 をコピー（保存で確定）'),
                    ('採血取得', '－', 'B', '', '検査システム連携（未設定）'),
                ]),
            ]))


def p_links():
    return ('<h1>6. 他画面との連携・自動計算</h1>' +
            table(['項目', 'カテ記録のデータ', '使う画面・内容'], [
                ('アプローチ・シース', 'exam.approach／exam.sheath', 'CAG/LVG のカテーテル欄（「カテ記録のアプローチを反映」でコピー）'),
                ('透視時間・造影剤・造影剤量', 'exam.fluoroTime／exam.contrast', 'PCI の J-PCI タブで同じ値を表示・編集'),
                ('DM・HT・HD・HL・既往歴・併存症', 'risk.*', 'PCI の J-PCI タブ（患者背景）で同じ値を表示（編集はカテ記録）'),
                ('Hb・Cr', 'labs.cbc.Hb／labs.admission.Cr', 'PCI の J-PCI タブ（患者背景）'),
                ('身長・体重（BSA）・HR', 'body.height／weight、hemo.values.HR', 'LVG の SV・EF・Index 算出'),
                ('施行日', 'report.header.studyDate', '年齢の計算、前回データ（前回からコピー・過去 CAG/Comment）の検索'),
            ], widths=['42mm', '52mm', None]) +
            '<h2>入力の制御</h2>' +
            table(['条件', '動作'], [
                ('Follow-up／その他1・2／担癌患者／大動脈疾患 が未チェック', '対応するテキスト欄は入力不可（グレー表示）'),
                ('検査値が基準範囲外', 'ピンク表示（保存は可能）。基準範囲は欄のツールチップに表示'),
                ('レポートが「確定」または閲覧権限のみ', '全項目が入力不可。画面上部に理由を表示'),
            ], widths=['70mm', None]) +
            '<h2>項目数</h2>' + table(['区分', '項目数'], [(k, (str(v), 'r')) for k, v in C.per.items()] + [(('合計', 'k'), (str(C.n), 'r k'))], widths=[None, '24mm']) +
            '<p class="small">項目数は一覧の行数です。繰返し（術者3名など）や複数キーを1行にまとめた項目は1と数えています。</p>')


PARTS = [
    ('ov', 1, '1. 画面の概要', p_overview),
    ('hd', 1, '2. 共通ヘッダー', p_header),
    ('ex', 1, '3. 検査情報', p_exam),
    ('st', 1, '4. 術者・血行動態・転帰・その他', p_staff),
    ('lb', 1, '5. 検査値・身体所見・危険因子', p_labs),
    ('ln', 1, '6. 他画面との連携・自動計算・項目数', p_links),
]

if __name__ == '__main__':
    build_doc('カテ記録 項目一覧', '画面項目・データパス・入力形式・選択肢・連携', 'React 版「カテ記録」画面（report.cathRecord）',
              RELATED, wrap(PARTS), G.ROOT / 'docs/design/items_cath_record.pdf')
