import { useState } from 'react';
import { Card, Form, Input, Switch, InputNumber, Select, Button, Typography, notification } from 'antd';

const { Title, Text } = Typography;

export default function Settings() {
  const [apiKey, setApiKey] = useState('');
  const [autoSync, setAutoSync] = useState(true);
  const [turnoverPeriod, setTurnoverPeriod] = useState(20);
  const [impactK, setImpactK] = useState(0.5);
  const [participationRate, setParticipationRate] = useState(10);
  const [theme, setTheme] = useState('dark');

  const handleSave = () => {
    // In a real implementation, this would save to the backend
    notification.success({ message: '設定を保存しました' });
  };

  return (
    <div>
      <Title level={3}>設定</Title>

      <Card title="J-Quants API設定" style={{ marginBottom: 16 }}>
        <Form layout="vertical" style={{ maxWidth: 500 }}>
          <Form.Item label="APIキー（リフレッシュトークン）">
            <Input.Password
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder="J-Quants APIキーを入力"
            />
          </Form.Item>
          <Form.Item label="起動時自動同期">
            <Switch checked={autoSync} onChange={setAutoSync} />
          </Form.Item>
        </Form>
      </Card>

      <Card title="分析パラメータ" style={{ marginBottom: 16 }}>
        <Form layout="vertical" style={{ maxWidth: 500 }}>
          <Form.Item label="回転日数デフォルト期間">
            <Select value={turnoverPeriod} onChange={setTurnoverPeriod} style={{ width: 200 }}>
              <Select.Option value={20}>20日</Select.Option>
              <Select.Option value={60}>60日</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="インパクト係数 (k)">
            <InputNumber value={impactK} onChange={v => setImpactK(v || 0.5)} min={0.01} max={2.0} step={0.01} style={{ width: 200 }} />
          </Form.Item>
          <Form.Item label="参加率上限デフォルト (%)">
            <InputNumber value={participationRate} onChange={v => setParticipationRate(v || 10)} min={1} max={100} style={{ width: 200 }} />
          </Form.Item>
        </Form>
      </Card>

      <Card title="表示設定" style={{ marginBottom: 16 }}>
        <Form layout="vertical" style={{ maxWidth: 500 }}>
          <Form.Item label="テーマ">
            <Select value={theme} onChange={setTheme} style={{ width: 200 }}>
              <Select.Option value="dark">ダーク</Select.Option>
              <Select.Option value="light">ライト</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Card>

      <Card title="データベース情報">
        <Text type="secondary">DBファイルパス: ./data/jq_stock.db</Text>
      </Card>

      <div style={{ marginTop: 16 }}>
        <Button type="primary" onClick={handleSave}>設定を保存</Button>
      </div>
    </div>
  );
}
