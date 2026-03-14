import { useQuery } from '@tanstack/react-query';
import { Card, Row, Col, Statistic, Typography } from 'antd';
import { DatabaseOutlined, StockOutlined, FundOutlined, SyncOutlined } from '@ant-design/icons';
import { getSyncStatus, getPortfolios } from '../api/client';

const { Title } = Typography;

export default function Dashboard() {
  const { data: syncStatus } = useQuery({
    queryKey: ['syncStatus'],
    queryFn: getSyncStatus,
  });

  const { data: portfolios } = useQuery({
    queryKey: ['portfolios'],
    queryFn: getPortfolios,
  });

  const totalPortfolioValue = portfolios?.reduce((sum, p) => sum + (p.total_value || 0), 0) || 0;
  const totalPnl = portfolios?.reduce((sum, p) => sum + (p.pnl || 0), 0) || 0;

  return (
    <div>
      <Title level={3}>ダッシュボード</Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="データ同期状態"
              value={syncStatus?.status === 'success' ? '同期済み' : syncStatus?.status === 'running' ? '同期中' : '未同期'}
              prefix={<SyncOutlined spin={syncStatus?.status === 'running'} />}
              valueStyle={{ color: syncStatus?.status === 'success' ? '#3f8600' : '#cf1322' }}
            />
            {syncStatus?.completed_at && (
              <div style={{ color: '#888', fontSize: 12, marginTop: 4 }}>
                最終更新: {new Date(syncStatus.completed_at).toLocaleString('ja-JP')}
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="ポートフォリオ数"
              value={portfolios?.length || 0}
              prefix={<FundOutlined />}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="合計評価額"
              value={totalPortfolioValue}
              prefix="¥"
              precision={0}
              groupSeparator=","
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="合計損益"
              value={totalPnl}
              prefix="¥"
              precision={0}
              groupSeparator=","
              valueStyle={{ color: totalPnl >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="クイックリンク">
            <Row gutter={16}>
              <Col span={8}>
                <Card size="small" hoverable onClick={() => window.location.hash = '#/screening'}>
                  <StockOutlined style={{ fontSize: 24, marginBottom: 8 }} />
                  <div>スクリーニング</div>
                  <div style={{ color: '#888', fontSize: 12 }}>条件を設定して銘柄を検索</div>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" hoverable onClick={() => window.location.hash = '#/portfolio'}>
                  <FundOutlined style={{ fontSize: 24, marginBottom: 8 }} />
                  <div>ポートフォリオ</div>
                  <div style={{ color: '#888', fontSize: 12 }}>保有銘柄の管理・分析</div>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" hoverable onClick={() => window.location.hash = '#/custom'}>
                  <DatabaseOutlined style={{ fontSize: 24, marginBottom: 8 }} />
                  <div>カスタム分析</div>
                  <div style={{ color: '#888', fontSize: 12 }}>回転日数・インパクト分析</div>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
