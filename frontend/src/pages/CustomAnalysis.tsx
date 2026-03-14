import { useState } from 'react';
import { Card, Typography } from 'antd';
import StockSearch from '../components/common/StockSearch';
import ImpactSimulator from '../components/impact/ImpactSimulator';

const { Title } = Typography;

export default function CustomAnalysis() {
  const [code, setCode] = useState('');

  return (
    <div>
      <Title level={3}>カスタム計算・インパクト分析</Title>

      <Card title="銘柄選択" style={{ marginBottom: 16 }}>
        <StockSearch onSelect={setCode} placeholder="分析する銘柄を検索..." />
        {code && <div style={{ marginTop: 8 }}>選択中: <strong>{code}</strong></div>}
      </Card>

      {code && <ImpactSimulator code={code} />}

      {!code && (
        <Card>
          <div style={{ color: '#888', textAlign: 'center', padding: 40 }}>
            銘柄を選択してインパクト分析を開始してください
          </div>
        </Card>
      )}
    </div>
  );
}
