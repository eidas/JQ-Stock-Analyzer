import { Button, Select, InputNumber, Space, Card, Tag } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ScreeningCondition } from '../../types';

const FIELD_OPTIONS = [
  { label: '--- 株価 ---', options: [
    { value: 'close', label: '終値' },
    { value: 'ytd_return', label: '年初来騰落率(%)' },
  ]},
  { label: '--- バリュエーション ---', options: [
    { value: 'per', label: 'PER' },
    { value: 'pbr', label: 'PBR' },
    { value: 'dividend_yield', label: '配当利回り(%)' },
  ]},
  { label: '--- 収益性 ---', options: [
    { value: 'roe', label: 'ROE(%)' },
    { value: 'operating_margin', label: '営業利益率(%)' },
    { value: 'ordinary_margin', label: '経常利益率(%)' },
  ]},
  { label: '--- 規模 ---', options: [
    { value: 'market_cap', label: '時価総額' },
  ]},
  { label: '--- 流動性 ---', options: [
    { value: 'turnover_days', label: '回転日数' },
    { value: 'avg_volume_20d', label: '20日平均出来高' },
  ]},
];

const OPERATOR_OPTIONS = [
  { value: 'gt', label: '>' },
  { value: 'lt', label: '<' },
  { value: 'gte', label: '>=' },
  { value: 'lte', label: '<=' },
  { value: 'between', label: '範囲' },
];

interface Props {
  conditions: ScreeningCondition[];
  onChange: (conditions: ScreeningCondition[]) => void;
  groupLogic: string;
  onGroupLogicChange: (logic: string) => void;
}

export default function ConditionBuilder({ conditions, onChange, groupLogic, onGroupLogicChange }: Props) {
  const addCondition = () => {
    const maxGroup = conditions.length > 0 ? Math.max(...conditions.map(c => c.group)) : 1;
    onChange([...conditions, { group: maxGroup, field: 'per', operator: 'lt', value: null }]);
  };

  const addGroup = () => {
    const maxGroup = conditions.length > 0 ? Math.max(...conditions.map(c => c.group)) : 0;
    onChange([...conditions, { group: maxGroup + 1, field: 'per', operator: 'lt', value: null }]);
  };

  const removeCondition = (index: number) => {
    onChange(conditions.filter((_, i) => i !== index));
  };

  const updateCondition = (index: number, updates: Partial<ScreeningCondition>) => {
    const updated = conditions.map((c, i) => i === index ? { ...c, ...updates } : c);
    onChange(updated);
  };

  // Group conditions by group number
  const groups: Record<number, { conditions: ScreeningCondition[]; indices: number[] }> = {};
  conditions.forEach((c, i) => {
    if (!groups[c.group]) groups[c.group] = { conditions: [], indices: [] };
    groups[c.group].conditions.push(c);
    groups[c.group].indices.push(i);
  });

  return (
    <Card size="small" title="フィルタ条件" extra={
      <Space>
        <Select value={groupLogic} onChange={onGroupLogicChange} size="small" style={{ width: 100 }}>
          <Select.Option value="and">AND</Select.Option>
          <Select.Option value="or">OR</Select.Option>
        </Select>
      </Space>
    }>
      {Object.entries(groups).map(([groupNum, group]) => (
        <div key={groupNum} style={{ marginBottom: 8, padding: 8, background: '#1a1a2e', borderRadius: 4 }}>
          <Tag color="blue">グループ {groupNum}</Tag>
          {group.indices.map((idx, j) => {
            const cond = conditions[idx];
            return (
              <Space key={idx} style={{ display: 'flex', marginTop: 4 }} align="center">
                {j > 0 && <Tag>AND</Tag>}
                <Select
                  value={cond.field}
                  onChange={v => updateCondition(idx, { field: v })}
                  style={{ width: 160 }}
                  size="small"
                  options={FIELD_OPTIONS}
                />
                <Select
                  value={cond.operator}
                  onChange={v => updateCondition(idx, { operator: v, value: v === 'between' ? [0, 0] : null })}
                  style={{ width: 80 }}
                  size="small"
                  options={OPERATOR_OPTIONS}
                />
                {cond.operator === 'between' ? (
                  <Space>
                    <InputNumber
                      size="small"
                      value={Array.isArray(cond.value) ? cond.value[0] : 0}
                      onChange={v => updateCondition(idx, { value: [v ?? 0, Array.isArray(cond.value) ? cond.value[1] : 0] })}
                      style={{ width: 100 }}
                    />
                    <span>〜</span>
                    <InputNumber
                      size="small"
                      value={Array.isArray(cond.value) ? cond.value[1] : 0}
                      onChange={v => updateCondition(idx, { value: [Array.isArray(cond.value) ? cond.value[0] : 0, v ?? 0] })}
                      style={{ width: 100 }}
                    />
                  </Space>
                ) : (
                  <InputNumber
                    size="small"
                    value={typeof cond.value === 'number' ? cond.value : undefined}
                    onChange={v => updateCondition(idx, { value: v })}
                    style={{ width: 120 }}
                  />
                )}
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  size="small"
                  onClick={() => removeCondition(idx)}
                />
              </Space>
            );
          })}
        </div>
      ))}
      <Space style={{ marginTop: 8 }}>
        <Button type="dashed" icon={<PlusOutlined />} onClick={addCondition} size="small">
          条件追加
        </Button>
        <Button type="dashed" onClick={addGroup} size="small">
          + グループ追加 (OR)
        </Button>
      </Space>
    </Card>
  );
}
