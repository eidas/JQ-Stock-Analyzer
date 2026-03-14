import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Tabs, Row, Col, Statistic, Tag, Spin, Typography, Segmented, Space } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { useStockSummary, useQuotes, useFinancials, useTechnicals } from '../hooks/useStockData';
import PriceChart from '../components/charts/PriceChart';
import FinancialChart from '../components/charts/FinancialChart';
import ImpactSimulator from '../components/impact/ImpactSimulator';

const { Title } = Typography;

const PERIODS: Record<string, number> = {
  '1M': 30, '3M': 90, '6M': 180, '1Y': 365, '3Y': 1095, '5Y': 1825,
};

const fmtCap = (v: number | null | undefined) => {
  if (!v) return '-';
  if (v >= 1e12) return `${(v / 1e12).toFixed(2)}兆円`;
  if (v >= 1e8) return `${(v / 1e8).toFixed(0)}億円`;
  return `${v.toLocaleString()}円`;
};

export default function StockDetail() {
  const { code } = useParams<{ code: string }>();
  const [period, setPeriod] = useState('1Y');
  const [indicators, setIndicators] = useState('sma');

  const { data: stock, isLoading } = useStockSummary(code || '');

  const today = new Date().toISOString().slice(0, 10);
  const fromDate = new Date(Date.now() - (PERIODS[period] || 365) * 86400000).toISOString().slice(0, 10);
  const { data: quotes } = useQuotes(code || '', fromDate, today);
  const { data: financials } = useFinancials(code || '');
  const { data: technicals } = useTechnicals(code || '', fromDate, today, indicators);

  if (isLoading || !stock) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const q = stock.quote;
  const m = stock.metrics;
  const isUp = (q.change_pct || 0) >= 0;

  return (
    <div>
      {/* Header */}
      <Card style={{ marginBottom: 16 }}>
        <Row align="middle" gutter={16}>
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              {stock.code} {stock.name}
            </Title>
            <Space>
              <Tag color="blue">{stock.market_segment}</Tag>
              <Tag>{stock.sector_33}</Tag>
            </Space>
          </Col>
          <Col flex="auto" />
          <Col>
            <Statistic
              value={q.close || 0}
              prefix="¥"
              precision={1}
              valueStyle={{ fontSize: 28 }}
            />
            <span style={{ color: isUp ? '#ef5350' : '#26a69a', fontSize: 16 }}>
              {isUp ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              {q.change != null ? ` ${q.change > 0 ? '+' : ''}${q.change}` : ''}
              {q.change_pct != null ? ` (${q.change_pct > 0 ? '+' : ''}${q.change_pct}%)` : ''}
            </span>
            <div style={{ color: '#888', fontSize: 12 }}>{q.date}</div>
          </Col>
        </Row>
      </Card>

      <Tabs items={[
        {
          key: 'summary',
          label: 'サマリー',
          children: (
            <Row gutter={[16, 16]}>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="PER" value={m.per || '-'} precision={1} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="PBR" value={m.pbr || '-'} precision={2} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="ROE" value={m.roe || '-'} suffix="%" precision={1} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="配当利回り" value={m.dividend_yield || '-'} suffix="%" precision={2} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="時価総額" value={fmtCap(m.market_cap)} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="自己資本比率" value={stock.financial.equity_ratio || '-'} suffix="%" precision={1} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="回転日数(20日)" value={m.turnover_days_20 || '-'} precision={1} suffix="日" /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="52週高値" value={stock.high_52w || '-'} prefix="¥" precision={1} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="52週安値" value={stock.low_52w || '-'} prefix="¥" precision={1} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="年初来" value={m.ytd_return || '-'} suffix="%" precision={1}
                  valueStyle={{ color: (m.ytd_return || 0) >= 0 ? '#3f8600' : '#cf1322' }} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small"><Statistic title="営業利益率" value={m.operating_margin || '-'} suffix="%" precision={1} /></Card>
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Card size="small">
                  <div style={{ color: '#888', fontSize: 12 }}>発行済株式数基準日</div>
                  <div>{stock.financial.disclosed_date || '-'}</div>
                </Card>
              </Col>
            </Row>
          ),
        },
        {
          key: 'chart',
          label: 'チャート',
          children: (
            <div>
              <Space style={{ marginBottom: 8 }}>
                <Segmented
                  options={Object.keys(PERIODS)}
                  value={period}
                  onChange={v => setPeriod(v as string)}
                />
              </Space>
              {quotes && <PriceChart data={quotes} overlays={technicals?.indicators} />}
              <div style={{ marginTop: 8 }}>
                <Segmented
                  options={[
                    { label: 'SMA', value: 'sma' },
                    { label: 'EMA', value: 'ema' },
                    { label: 'ボリンジャー', value: 'bollinger' },
                    { label: '一目均衡表', value: 'ichimoku' },
                    { label: 'RSI', value: 'rsi' },
                    { label: 'MACD', value: 'macd' },
                  ]}
                  value={indicators}
                  onChange={v => setIndicators(v as string)}
                />
              </div>
            </div>
          ),
        },
        {
          key: 'financial',
          label: '財務',
          children: financials ? <FinancialChart data={financials} /> : <Spin />,
        },
        {
          key: 'liquidity',
          label: '流動性・回転日数',
          children: <ImpactSimulator code={code || ''} />,
        },
      ]} />
    </div>
  );
}
