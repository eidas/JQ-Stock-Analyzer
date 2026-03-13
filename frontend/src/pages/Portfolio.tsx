import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Button, Modal, Input, Form, InputNumber, Row, Col, Statistic, Space, Popconfirm, notification, Empty } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import HoldingsTable from '../components/portfolio/HoldingsTable';
import AllocationChart from '../components/portfolio/AllocationChart';
import StockSearch from '../components/common/StockSearch';
import { getPortfolios, getPortfolio, createPortfolio, deletePortfolio, addPortfolioItem, deletePortfolioItem } from '../api/client';

export default function Portfolio() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showAddItem, setShowAddItem] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [addCode, setAddCode] = useState('');
  const [addShares, setAddShares] = useState(100);
  const [addCost, setAddCost] = useState(0);

  const { data: portfolios } = useQuery({
    queryKey: ['portfolios'],
    queryFn: getPortfolios,
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['portfolio', selectedId],
    queryFn: () => getPortfolio(selectedId!),
    enabled: !!selectedId,
  });

  const createMutation = useMutation({
    mutationFn: () => createPortfolio(newName, newDesc),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      setShowCreate(false);
      setNewName('');
      setNewDesc('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deletePortfolio(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      setSelectedId(null);
    },
  });

  const addItemMutation = useMutation({
    mutationFn: () => addPortfolioItem(selectedId!, { code: addCode, shares: addShares, avg_cost: addCost }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio', selectedId] });
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      setShowAddItem(false);
      setAddCode('');
      notification.success({ message: '銘柄を追加しました' });
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => deletePortfolioItem(selectedId!, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio', selectedId] });
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });

  return (
    <div>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>ポートフォリオ</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>
          新規作成
        </Button>
      </Space>

      <Row gutter={[16, 16]}>
        {portfolios?.map(p => (
          <Col xs={24} sm={12} md={8} key={p.id}>
            <Card
              hoverable
              onClick={() => setSelectedId(p.id)}
              style={{ borderColor: selectedId === p.id ? '#1890ff' : undefined }}
              extra={
                <Popconfirm title="削除しますか？" onConfirm={(e) => { e?.stopPropagation(); deleteMutation.mutate(p.id); }}>
                  <Button type="text" danger icon={<DeleteOutlined />} size="small" onClick={e => e.stopPropagation()} />
                </Popconfirm>
              }
            >
              <Statistic title={p.name} value={p.total_value || 0} prefix="¥" precision={0} groupSeparator="," />
              <div style={{ marginTop: 8 }}>
                <span style={{ color: (p.pnl || 0) >= 0 ? '#3f8600' : '#cf1322' }}>
                  損益: ¥{(p.pnl || 0).toLocaleString()} ({p.pnl_pct || 0}%)
                </span>
                <span style={{ color: '#888', marginLeft: 8 }}>{p.item_count}銘柄</span>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {selectedId && detail && (
        <div style={{ marginTop: 24 }}>
          <Space style={{ marginBottom: 12, width: '100%', justifyContent: 'space-between' }}>
            <h3>{detail.name} — 合計評価額: ¥{detail.total_value.toLocaleString()}</h3>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowAddItem(true)}>
              銘柄追加
            </Button>
          </Space>

          <Row gutter={16}>
            <Col span={16}>
              <HoldingsTable
                items={detail.items}
                loading={detailLoading}
                onDelete={(itemId) => deleteItemMutation.mutate(itemId)}
              />
            </Col>
            <Col span={8}>
              <Card title="セクター別構成比" size="small">
                <AllocationChart items={detail.items} />
              </Card>
            </Col>
          </Row>
        </div>
      )}

      {!selectedId && portfolios?.length === 0 && (
        <Empty description="ポートフォリオがありません" style={{ marginTop: 80 }} />
      )}

      {/* Create Portfolio Modal */}
      <Modal title="ポートフォリオ作成" open={showCreate} onOk={() => createMutation.mutate()} onCancel={() => setShowCreate(false)}>
        <Form layout="vertical">
          <Form.Item label="名前">
            <Input value={newName} onChange={e => setNewName(e.target.value)} />
          </Form.Item>
          <Form.Item label="説明">
            <Input.TextArea value={newDesc} onChange={e => setNewDesc(e.target.value)} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Add Item Modal */}
      <Modal title="銘柄追加" open={showAddItem} onOk={() => addItemMutation.mutate()} onCancel={() => setShowAddItem(false)}>
        <Form layout="vertical">
          <Form.Item label="銘柄">
            <StockSearch onSelect={setAddCode} />
            {addCode && <div style={{ marginTop: 4 }}>選択: {addCode}</div>}
          </Form.Item>
          <Form.Item label="保有株数">
            <InputNumber value={addShares} onChange={v => setAddShares(v || 0)} min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="平均取得単価">
            <InputNumber value={addCost} onChange={v => setAddCost(v || 0)} min={0} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
