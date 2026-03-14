import { useState } from 'react';
import { Card, Form, InputNumber, Button, Statistic, Row, Col, Table, Slider } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useImpact } from '../../hooks/useStockData';


interface Props {
  code: string;
}

export default function ImpactSimulator({ code }: Props) {
  const [params, setParams] = useState({
    quantity: 100000,
    days: 1,
    participation_rate: 0.1,
    vol_period: 20,
  });
  const [execute, setExecute] = useState(false);

  const { data: result, isLoading } = useImpact(code, params, execute);

  const handleRun = () => {
    setExecute(true);
  };

  const scheduleColumns = [
    { title: '日目', dataIndex: 'day', key: 'day' },
    { title: '売買数量', dataIndex: 'quantity', key: 'quantity', render: (v: number) => v?.toLocaleString() },
    { title: '参加率', dataIndex: 'participation_rate', key: 'participation_rate', render: (v: number) => `${(v * 100).toFixed(2)}%` },
  ];

  return (
    <div>
      <Card title="インパクト分析シミュレーター" size="small">
        <Form layout="inline" style={{ marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
          <Form.Item label="売買数量（株）">
            <InputNumber
              value={params.quantity}
              onChange={v => { setParams(p => ({ ...p, quantity: v || 0 })); setExecute(false); }}
              min={1}
              step={10000}
              style={{ width: 150 }}
            />
          </Form.Item>
          <Form.Item label="執行日数">
            <InputNumber
              value={params.days}
              onChange={v => { setParams(p => ({ ...p, days: v || 1 })); setExecute(false); }}
              min={1}
              max={60}
              style={{ width: 80 }}
            />
          </Form.Item>
          <Form.Item label="参加率上限">
            <Slider
              value={params.participation_rate * 100}
              onChange={v => { setParams(p => ({ ...p, participation_rate: v / 100 })); setExecute(false); }}
              min={1}
              max={50}
              step={1}
              style={{ width: 150 }}
              tooltip={{ formatter: (v) => `${v}%` }}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" onClick={handleRun} loading={isLoading}>
              分析実行
            </Button>
          </Form.Item>
        </Form>

        {result && !('error' in result) && (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Statistic
                  title="推定インパクトコスト"
                  value={result.result.estimated_impact_pct}
                  suffix="%"
                  precision={4}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="推定インパクト（円）"
                  value={result.result.estimated_impact_yen}
                  prefix="¥"
                  precision={0}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="最小執行日数"
                  value={result.result.min_execution_days}
                  suffix="日"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="日次ボラティリティ"
                  value={(result.market_data.daily_volatility || 0) * 100}
                  suffix="%"
                  precision={2}
                />
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <h4>日別執行スケジュール</h4>
                <Table
                  columns={scheduleColumns}
                  dataSource={result.result.daily_schedule}
                  rowKey="day"
                  size="small"
                  pagination={false}
                />
              </Col>
              <Col span={12}>
                <h4>出来高対比</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={result.result.daily_schedule}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="day" tick={{ fill: '#aaa' }} label={{ value: '日目', position: 'bottom' }} />
                    <YAxis tick={{ fill: '#aaa' }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="quantity" name="売買数量" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </Col>
            </Row>
          </>
        )}
      </Card>
    </div>
  );
}
