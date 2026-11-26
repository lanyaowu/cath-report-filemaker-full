import { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { Btn, Modal, Tabs } from '../common/ui';
import type { Masters } from '../../types/model';
import { DEVICE_CATEGORIES } from '../../constants/options';
import { useOptionList } from '../../form/OptionsContext';

/** 術者・紹介病院・デバイスマスタの編集（「デバイスマスタを編集」「マスタ編集」） */
export function MasterDialog({ onClose, initialTab = 'devices' }: { onClose: () => void; initialTab?: 'doctors' | 'hospitals' | 'devices' }) {
  const app = useApp();
  const [m, setM] = useState<Masters>(app.masters);
  const [tab, setTab] = useState<string>(initialTab);
  const deviceCategories = useOptionList(DEVICE_CATEGORIES).map((o) => o.value);

  const listEditor = (key: 'doctors' | 'hospitals') => (
    <div>
      {m[key].map((v, i) => (
        <div key={i} className="f" style={{ marginBottom: 2 }}>
          <input className="inp" style={{ width: 260 }} value={v} onChange={(e) => setM({ ...m, [key]: m[key].map((x, j) => (j === i ? e.target.value : x)) })} />
          <Btn small onClick={() => setM({ ...m, [key]: m[key].filter((_, j) => j !== i) })}>削除</Btn>
        </div>
      ))}
      <Btn small onClick={() => setM({ ...m, [key]: [...m[key], ''] })}>＋ 追加</Btn>
    </div>
  );

  return (
    <Modal
      title="マスタ編集"
      onClose={onClose}
      width={640}
      footer={
        <>
          <Btn
            kind="primary"
            onClick={async () => {
              await app.saveMasters({
                doctors: m.doctors.filter(Boolean),
                hospitals: m.hospitals.filter(Boolean),
                devices: m.devices.filter((d) => d.name),
              });
              onClose();
            }}
          >
            保存
          </Btn>
          <Btn onClick={onClose}>キャンセル</Btn>
        </>
      }
    >
      <Tabs
        small
        active={tab}
        onChange={setTab}
        tabs={[
          { key: 'devices', label: 'デバイス' },
          { key: 'doctors', label: '術者・医師' },
          { key: 'hospitals', label: '紹介病院' },
        ]}
      />
      <div className="scroll" style={{ maxHeight: 380, paddingTop: 6 }}>
        {tab === 'doctors' && listEditor('doctors')}
        {tab === 'hospitals' && listEditor('hospitals')}
        {tab === 'devices' && (
          <div>
            {m.devices.map((d, i) => (
              <div key={i} className="f" style={{ marginBottom: 2 }}>
                <input
                  className="inp"
                  list="dev-cat"
                  style={{ width: 120 }}
                  value={d.category}
                  onChange={(e) => setM({ ...m, devices: m.devices.map((x, j) => (j === i ? { ...x, category: e.target.value } : x)) })}
                />
                <input
                  className="inp"
                  style={{ width: 260 }}
                  value={d.name}
                  onChange={(e) => setM({ ...m, devices: m.devices.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)) })}
                />
                <Btn small onClick={() => setM({ ...m, devices: m.devices.filter((_, j) => j !== i) })}>削除</Btn>
              </div>
            ))}
            <datalist id="dev-cat">
              {[...deviceCategories, 'Guiding', 'Micro', 'GW'].map((c) => (
                <option key={c} value={c} />
              ))}
            </datalist>
            <Btn small onClick={() => setM({ ...m, devices: [...m.devices, { category: '', name: '' }] })}>＋ 追加</Btn>
          </div>
        )}
      </div>
    </Modal>
  );
}
