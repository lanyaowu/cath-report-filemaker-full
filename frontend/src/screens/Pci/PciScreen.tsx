import { useState } from 'react';
import { Scope } from '../../form/FormContext';
import { Tabs } from '../../components/common/ui';
import { ScreenFrame } from '../../components/layout/ScreenFrame';
import { MasterDialog } from '../../components/dialogs/MasterDialog';
import { useApp } from '../../state/AppContext';
import { hasAnyValue } from '../../utils/path';
import { BasicTab } from './BasicTab';
import { BifCtoTab, ComplicationTab, DeviceTab, MorphTab } from './LesionTabs';
import { JpciTab } from './JpciTab';
import { BleedingRiskTab } from './BleedingRiskTab';
import { AmiTab } from './AmiTab';
import { SearchTab } from './SearchTab';
import { ReferenceTab } from './ReferenceTab';

const TABS = [
  { key: 'basic', label: '基本', arrow: true },
  { key: 'morph', label: '病変形態', arrow: true },
  { key: 'device', label: 'Device', arrow: true },
  { key: 'bifcto', label: 'Bif/CTO', arrow: true },
  { key: 'comp', label: 'Complication', arrow: true },
  { key: 'jpci', label: 'J-PCI', arrow: true },
  { key: 'risk', label: '出血・血栓リスク' },
  { key: 'ami', label: 'AMI' },
  { key: 'search', label: '検索用' },
  { key: 'ref', label: '参考資料' },
];

/** PCI */
export function PciScreen() {
  const [tab, setTab] = useState('basic');
  const [master, setMaster] = useState(false);
  const pci = useApp().draft!.report.pci;
  const has: Record<string, boolean> = {
    basic: hasAnyValue(pci.basic),
    morph: pci.lesions.some((l) => !!l.type || Object.values(l.morph).some(Boolean)),
    device: pci.lesions.some((l) => hasAnyValue(l.device)),
    bifcto: pci.lesions.some((l) => hasAnyValue(l.bif) || hasAnyValue(l.cto)),
    comp: pci.lesions.some((l) => hasAnyValue(l.comp)) || hasAnyValue(pci.patientComp),
    jpci: hasAnyValue(pci.jpci),
    risk: hasAnyValue(pci.risk),
    ami: hasAnyValue(pci.ami),
  };

  return (
    <ScreenFrame
      headerExtra={
        <button type="button" className="link-btn" onClick={() => setMaster(true)}>
          📄 デバイスマスタを編集
        </button>
      }
    >
      <Scope path="/report.pci">
        <Tabs active={tab} onChange={setTab} tabs={TABS.map((t) => ({ ...t, hasData: has[t.key] }))} />
        <div className="tab-body">
          {tab === 'basic' && <BasicTab />}
          {tab === 'morph' && <MorphTab />}
          {tab === 'device' && <DeviceTab />}
          {tab === 'bifcto' && <BifCtoTab />}
          {tab === 'comp' && <ComplicationTab />}
          {tab === 'jpci' && <JpciTab />}
          {tab === 'risk' && <BleedingRiskTab />}
          {tab === 'ami' && <AmiTab />}
          {tab === 'search' && <SearchTab />}
          {tab === 'ref' && <ReferenceTab />}
        </div>
      </Scope>
      {master && <MasterDialog onClose={() => setMaster(false)} />}
    </ScreenFrame>
  );
}
