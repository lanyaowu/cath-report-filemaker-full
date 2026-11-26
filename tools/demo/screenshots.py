#!/usr/bin/env python3
"""デモ HTML から全画面の PNG を作成（Playwright + Chrome）
usage: python3 tools/demo/screenshots.py [demo.html] [outdir]
"""
import asyncio, re, sys, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
HTML = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'demo/cath-report-demo.html').resolve()
OUT = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / 'demo/screenshots')
OUT.mkdir(parents=True, exist_ok=True)
SLUG = {
    '一覧': 'list', '新規作成ダイアログ': 'dialog_new_report', '保存先設定ダイアログ': 'dialog_storage_settings', 'マスタダイアログ': 'dialog_masters',
    '患者情報入力': 'patient', 'カテ記録_検査値・危険因子': 'cath_labs_risk', 'カテ記録_入院時血算': 'cath_cbc',
    'カテ記録_甲状腺': 'cath_endocrine_urine', 'カテ記録_退院時(カテ時)': 'cath_discharge_labs', 'カテ記録_血ガス_AQT': 'cath_bloodgas_aqt',
    'カテ記録_旧項目': 'cath_legacy_labs', 'CAG': 'cag', 'LVG': 'lvg', 'Restudy': 'restudy',
    'PCI_基本': 'pci_basic', 'PCI_病変形態': 'pci_lesion_morphology', 'PCI_Device': 'pci_device', 'PCI_Bif_CTO': 'pci_bif_cto',
    'PCI_Complication': 'pci_complication', 'PCI_J-PCI': 'pci_jpci', 'PCI_出血・血栓リスク': 'pci_bleeding_thrombus_risk',
    'PCI_検索用': 'pci_search', 'PCI_参考資料_分岐部病変タイプ': 'pci_ref_bifurcation_type',
    'PCI_参考資料_分岐部治療ストラテジー': 'pci_ref_bifurcation_strategy', 'PCI_参考資料_Medina分類': 'pci_ref_medina',
    'Pressure_IVUS_Lesion1': 'pressure_ivus_lesion1', '画像': 'images',
    'カンファレンス_基本・血行動態・危険因子': 'conf_basic', 'カンファレンス_Previous PCI': 'conf_previous_pci',
    'カンファレンス_Scintigram': 'conf_scintigram', 'カンファレンス_MDCT': 'conf_mdct', 'カンファレンス_UCG': 'conf_ucg',
    'カンファレンス_Treadmill_処方': 'conf_treadmill_rx', 'カンファレンス_臨床診断_感染症': 'conf_clinical_infection',
    'カンファレンス_既往歴_経過': 'conf_history_course', 'カンファレンス_退院時処方': 'conf_discharge_rx', 'MACE': 'mace',
    'PCI_AMI': 'pci_ami', 'PCI_AMI_時間経過シート': 'pci_ami_timeline_sheet', 'Pressure_IVUS_PressureWire': 'pressure_wire',
    'PCPS': 'pcps', '変更あり_保存ボタン赤': 'edit_save_button_red', '遷移確認ダイアログ': 'dialog_discard_confirm',
    'キャンセル後_変更項目黄色': 'cancel_changed_fields_yellow', '確定済み_編集ロック': 'locked_confirmed_report', '集計': 'stats',
    '確定前の確認ダイアログ': 'dialog_confirm_check', '検査報告書': 'report_print',
    '選択値マスタダイアログ': 'dialog_option_master', '選択値マスタ_標準の分類': 'dialog_option_master_fixed',
    '選択値マスタ_編集中': 'dialog_option_master_edit', '選択値マスタ_PCIの選択肢に反映': 'option_master_applied',
    '監査ログダイアログ': 'dialog_audit_log', '監査ログ_変わった項目': 'dialog_audit_log_changes',
    '項目ごとの変更履歴': 'dialog_report_history',
}


def write_index(index):
    """対応表: index.csv（Excel 用 UTF-8 BOM）と index.html（サムネイル一覧）"""
    with open(OUT / 'index.csv', 'w', encoding='utf-8-sig', newline='') as f:
        f.write('No,ファイル名,画面\r\n')
        for i, (fn, jp) in enumerate(index, 1):
            f.write(f'{i},{fn},"{jp}"\r\n')
    cards = ''.join(
        f'<figure><a href="{fn}" target="_blank"><img src="{fn}" loading="lazy"></a><figcaption><b>{i:02d}</b> {jp}<br><code>{fn}</code></figcaption></figure>'
        for i, (fn, jp) in enumerate(index, 1))
    (OUT / 'index.html').write_text(
        '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>心カテーテルレポート 画面一覧</title>'
        '<style>body{font-family:"Meiryo UI",sans-serif;background:#eef2ef;margin:16px}'
        '.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}'
        'figure{margin:0;background:#fff;border:1px solid #b8c4c0;padding:6px}'
        'img{width:100%;height:200px;object-fit:cover;object-position:top;border:1px solid #ddd}'
        'figcaption{font-size:13px;margin-top:4px}code{font-size:11px;color:#678}</style></head>'
        f'<body><h2>心カテーテルレポート 画面一覧（{len(index)}画面）</h2><div class="g">{cards}</div></body></html>',
        encoding='utf-8')


FULL = '.app{height:auto!important}.app-body{min-height:100vh}.main{overflow:visible!important}.demo-banner{display:none}'

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--lang=ja-JP'])
        ctx = await b.new_context(viewport={'width': 1600, 'height': 900}, locale='ja-JP', device_scale_factor=1)
        pg = await ctx.new_page()
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        await pg.goto(HTML.as_uri())
        await pg.add_style_tag(content=FULL)
        await pg.wait_for_timeout(600)
        n = [0]

        index = []

        async def shot(name, full=True, element=None):
            # Windows での文字化けを避けるためファイル名は英数字（日本語名は index に記載）
            n[0] += 1
            await pg.wait_for_timeout(250)
            fname = f'{n[0]:02d}_{SLUG.get(name, "screen")}.png'
            if element:  # 画面の上に重ねた表示（検査報告書）は、ウィンドウを縦に広げて要素全体を撮る
                vp = pg.viewport_size
                h = await pg.locator(element).evaluate('e => Math.ceil(e.getBoundingClientRect().height) + 120')
                await pg.set_viewport_size({'width': vp['width'], 'height': max(vp['height'], h)})
                await pg.wait_for_timeout(300)
                await pg.locator(element).screenshot(path=str(OUT / fname))
                await pg.set_viewport_size(vp)
            else:
                await pg.screenshot(path=str(OUT / fname), full_page=full)
            index.append((fname, name))

        async def nav(label):
            await pg.locator('.sidenav .nav-item > button:first-child').filter(has_text=re.compile(f'^{re.escape(label)}$')).click()
            await pg.wait_for_timeout(200)

        async def tab(label, small=False):
            sel = '.tabs-sm button.tab' if small else '.tabs:not(.tabs-sm) button.tab'
            await pg.locator(sel).filter(has_text=re.compile(f'^{re.escape(label)}')).first.click()
            await pg.wait_for_timeout(150)

        async def open_rec(cine):
            await nav('一覧')
            await pg.locator(f'tr:has-text("{cine}") .open-btn').click()
            await pg.wait_for_timeout(300)

        # ログイン画面（番号 00。他の画像の番号は変えない）→ 管理者でログイン（全ボタンを有効にして撮る）
        await pg.wait_for_selector('.login-screen')
        await pg.wait_for_timeout(250)
        await pg.screenshot(path=str(OUT / '00_login.png'))
        index.append(('00_login.png', 'ログイン'))
        await pg.fill('#login-user', 'admin')
        await pg.fill('#login-pass', 'demo-admin')
        await pg.click('.login-btn')
        await pg.wait_for_selector('.topbar')
        await pg.wait_for_timeout(2600)  # ログインのお知らせ（トースト）が消えるまで

        # 一覧・ダイアログ
        await shot('一覧')
        await pg.get_by_role('button', name='✎ 新規作成').click()
        await shot('新規作成ダイアログ', False)
        await pg.locator('.modal .x').click()
        await pg.locator('.topbar button', has_text='Local').click()
        await shot('保存先設定ダイアログ', False)
        await pg.locator('.modal-f button', has_text='キャンセル').click()
        await pg.locator('.topbar button', has_text='マスタ').click()
        await shot('マスタダイアログ', False)
        await pg.locator('.modal .x').click()

        await open_rec('C26-1101')
        await nav('患者情報入力'); await shot('患者情報入力')
        await nav('カテ記録'); await shot('カテ記録_検査値・危険因子')
        for t in ['入院時血算', '甲状腺・副腎系']:
            await tab(t, True); await shot(f'カテ記録_{t.split("・")[0]}')
        for t in ['退院時(カテ時)', '血ガス/AQT', '旧項目']:
            await tab(t); await shot(f'カテ記録_{t.replace("/", "_")}')
        await tab('入院時(カテ時)')

        await nav('CAG/LVG'); await shot('CAG')
        await tab('LVG'); await shot('LVG')
        await nav('Restudy'); await shot('Restudy')
        await nav('PCI')
        for t in ['基本', '病変形態', 'Device', 'Bif/CTO', 'Complication', 'J-PCI', '出血・血栓リスク', '検索用']:
            await tab(t); await shot(f'PCI_{t.replace("/", "_")}')
        await tab('参考資料')
        for t in ['分岐部病変タイプ', '分岐部治療ストラテジー', 'Medina分類']:
            await tab(t, True); await shot(f'PCI_参考資料_{t}')
        await nav('Pressure/IVUS'); await tab('Lesion 1'); await shot('Pressure_IVUS_Lesion1')
        await nav('画像'); await shot('画像')
        await nav('カンファレンス')
        for t in ['基本・血行動態・危険因子', 'Previous PCI', 'Scintigram', 'MDCT', 'UCG', 'Treadmill/処方', '臨床診断/感染症', '既往歴/経過', '退院時処方']:
            await tab(t); await shot(f'カンファレンス_{t.replace("/", "_")}')
        await nav('MACE'); await shot('MACE')

        await open_rec('C26-1102')
        await nav('PCI'); await tab('AMI'); await shot('PCI_AMI')
        await pg.get_by_role('button', name='🖨 STEMI時間経過シート').click()
        await shot('PCI_AMI_時間経過シート', False)
        await pg.locator('.modal .x').click()

        await open_rec('C26-1103')
        await nav('Pressure/IVUS'); await shot('Pressure_IVUS_PressureWire')

        await open_rec('C26-1104')
        await nav('PCPS'); await shot('PCPS')

        # 変更 → 遷移確認ダイアログ → キャンセルで黄色表示
        await open_rec('C26-1101')
        await nav('カテ記録')
        await pg.locator('[data-path="report.cathRecord.exam.diagnosis"]').fill('AP（労作性）')
        await pg.locator('[data-path="report.cathRecord.exam.contrast.volume"]').fill('80')
        await pg.locator('[data-path="report.cathRecord.labs.admission.AST"]').fill('35')
        await shot('変更あり_保存ボタン赤', False)
        await nav('CAG/LVG')
        await shot('遷移確認ダイアログ', False)
        await pg.locator('.modal-f button', has_text='キャンセル').click()
        await shot('キャンセル後_変更項目黄色', False)
        await nav('CAG/LVG')
        await pg.locator('.modal-f button', has_text='放棄').click()

        # 参照項目（他画面が主）の表示
        await open_rec('C26-1107')
        await nav('カテ記録'); await shot('確定済み_編集ロック')

        # 確定前の確認（未入力の必須項目・自動判定との食い違い）と検査報告書
        await open_rec('C26-1105')
        await nav('PCI')
        await pg.locator('.badge-status').click(); await pg.wait_for_timeout(300)
        await shot('確定前の確認ダイアログ', False)
        await pg.locator('.modal-f button', has_text='キャンセル').click(); await pg.wait_for_timeout(200)
        await pg.locator('button', has_text='検査報告書').first.click(); await pg.wait_for_timeout(500)
        await shot('検査報告書', element='.print-page')
        await pg.locator('.print-bar button', has_text='閉じる').click(); await pg.wait_for_timeout(200)

        await nav('集計'); await shot('集計')

        # ---- 選択値マスタ（統合版で追加。番号は末尾に続ける）
        await pg.locator('.topbar button', has_text='選択値').click(); await pg.wait_for_timeout(300)
        await shot('選択値マスタダイアログ', False)
        await pg.locator('.optm-cat', has_text='TIMI 分類').click()
        await shot('選択値マスタ_標準の分類', False)
        await pg.locator('.optm-cat', has_text='補助循環・サポート').click(); await pg.wait_for_timeout(150)
        await pg.locator('.optm-tbl tbody tr:nth-child(1) input[type=checkbox]').uncheck()
        await pg.locator('.modal button', has_text='＋ 追加').click()
        await pg.locator('.optm-tbl tbody tr:last-child td:nth-child(3) input').fill('ECMO')
        await shot('選択値マスタ_編集中', False)
        await pg.locator('.modal-f button', has_text='保存').click(); await pg.wait_for_timeout(400)
        await pg.locator('.modal-f button', has_text='閉じる').click(); await pg.wait_for_timeout(200)
        await open_rec('C26-1101')
        await nav('PCI'); await tab('基本')
        await pg.locator('select[data-path$="basic.support"]').evaluate(
            "s => { s.size = s.options.length; s.style.height = 'auto'; s.style.position = 'relative'; s.style.zIndex = 50; s.style.outline = '3px solid #e02020'; s.scrollIntoView({block: 'center'}); }")
        await shot('選択値マスタ_PCIの選択肢に反映', False)

        # ---- 監査ログ・変更履歴（統合版で追加）：カテ記録を変えて保存してから撮る
        await nav('カテ記録')
        await pg.locator('[data-path="report.cathRecord.exam.contrast.volume"]').fill('120')
        await pg.locator('.tb-save').click(); await pg.wait_for_timeout(2600)
        await pg.locator('.topbar button', has_text='監査ログ').click(); await pg.wait_for_timeout(500)
        await shot('監査ログダイアログ', False)
        await pg.locator('.audit-row.has-changes').first.click(); await pg.wait_for_timeout(200)
        await shot('監査ログ_変わった項目', False)
        await pg.locator('.modal-f button', has_text='閉じる').click(); await pg.wait_for_timeout(200)
        await pg.locator('button', has_text='項目ごとの変更履歴').click(); await pg.wait_for_timeout(500)
        await shot('項目ごとの変更履歴', False)
        await b.close()
        write_index(index)
        print(f'{n[0]} screenshots -> {OUT}')
        if errors:
            print('PAGE ERRORS:', *errors[:10], sep='\n')

asyncio.run(main())
