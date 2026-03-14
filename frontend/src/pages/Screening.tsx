import { useState, useCallback } from 'react';
import { Button, Space, Select, Input, Modal, notification } from 'antd';
import { SearchOutlined, SaveOutlined, DownloadOutlined } from '@ant-design/icons';
import ConditionBuilder from '../components/screening/ConditionBuilder';
import ResultTable from '../components/screening/ResultTable';
import { usePresets, useSavePreset, useDeletePreset } from '../hooks/useScreening';
import { searchScreening, exportScreening } from '../api/client';
import type { ScreeningCondition, ScreeningResponse } from '../types';

export default function Screening() {
  const [conditions, setConditions] = useState<ScreeningCondition[]>([]);
  const [groupLogic, setGroupLogic] = useState('and');
  const [sortBy, setSortBy] = useState('code');
  const [sortOrder, setSortOrder] = useState('asc');
  const [page, setPage] = useState(1);
  const [results, setResults] = useState<ScreeningResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [showSave, setShowSave] = useState(false);

  const { data: presets } = usePresets();
  const savePresetMutation = useSavePreset();
  useDeletePreset(); // Available for future use

  const handleSearch = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const data = await searchScreening({
        conditions,
        group_logic: groupLogic,
        sort_by: sortBy,
        sort_order: sortOrder,
        page: p,
        per_page: 50,
        market_segments: [],
        sectors_33: [],
      });
      setResults(data);
      setPage(p);
    } catch (e) {
      notification.error({ message: 'スクリーニングエラー' });
    } finally {
      setLoading(false);
    }
  }, [conditions, groupLogic, sortBy, sortOrder]);

  const handleExport = async () => {
    try {
      const blob = await exportScreening({
        conditions,
        group_logic: groupLogic,
        sort_by: sortBy,
        sort_order: sortOrder,
        page: 1,
        per_page: 50,
        market_segments: [],
        sectors_33: [],
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'screening_results.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      notification.error({ message: 'エクスポートエラー' });
    }
  };

  const handleSavePreset = () => {
    if (!presetName) return;
    savePresetMutation.mutate({
      name: presetName,
      conditions_json: JSON.stringify({ conditions, group_logic: groupLogic }),
    });
    setShowSave(false);
    setPresetName('');
    notification.success({ message: 'プリセットを保存しました' });
  };

  const handleLoadPreset = (conditionsJson: string) => {
    try {
      const parsed = JSON.parse(conditionsJson);
      setConditions(parsed.conditions || []);
      setGroupLogic(parsed.group_logic || 'and');
    } catch {
      notification.error({ message: 'プリセットの読み込みに失敗しました' });
    }
  };

  return (
    <div>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }} align="center">
        <h2 style={{ margin: 0 }}>スクリーニング</h2>
        <Space>
          <Select
            placeholder="プリセット選択"
            style={{ width: 200 }}
            allowClear
            onChange={(_, option: any) => option && handleLoadPreset(option.conditions_json)}
            options={presets?.map(p => ({
              value: p.id,
              label: p.name,
              conditions_json: p.conditions_json,
            }))}
          />
          <Button icon={<SaveOutlined />} onClick={() => setShowSave(true)}>保存</Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>CSV</Button>
        </Space>
      </Space>

      <ConditionBuilder
        conditions={conditions}
        onChange={setConditions}
        groupLogic={groupLogic}
        onGroupLogicChange={setGroupLogic}
      />

      <div style={{ marginTop: 12, marginBottom: 12 }}>
        <Button type="primary" icon={<SearchOutlined />} onClick={() => handleSearch(1)} loading={loading}>
          検索
        </Button>
      </div>

      {results && (
        <ResultTable
          results={results.results}
          total={results.total}
          page={page}
          perPage={results.per_page}
          loading={loading}
          onPageChange={(p) => handleSearch(p)}
          onSortChange={(field, order) => {
            setSortBy(field);
            setSortOrder(order);
          }}
        />
      )}

      <Modal
        title="プリセット保存"
        open={showSave}
        onOk={handleSavePreset}
        onCancel={() => setShowSave(false)}
      >
        <Input
          placeholder="プリセット名"
          value={presetName}
          onChange={e => setPresetName(e.target.value)}
        />
      </Modal>
    </div>
  );
}
