import { Table, Button, Popconfirm } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { PortfolioItem } from '../../types';

interface Props {
  items: PortfolioItem[];
  loading: boolean;
  onDelete: (itemId: number) => void;
}

const fmt = (v: number | null, d = 2) =>
  v !== null && v !== undefined ? v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d }) : '-';

export default function HoldingsTable({ items, loading, onDelete }: Props) {
  const navigate = useNavigate();

  const columns = [
    {
      title: 'コード',
      dataIndex: 'code',
      render: (code: string) => <a onClick={() => navigate(`/stocks/${code}`)}>{code}</a>,
    },
    { title: '銘柄名', dataIndex: 'name', ellipsis: true },
    { title: '保有株数', dataIndex: 'shares', align: 'right' as const, render: (v: number) => v?.toLocaleString() },
    { title: '取得単価', dataIndex: 'avg_cost', align: 'right' as const, render: (v: number) => fmt(v, 1) },
    { title: '現在値', dataIndex: 'current_price', align: 'right' as const, render: (v: number | null) => fmt(v, 1) },
    { title: '評価額', dataIndex: 'eval_amount', align: 'right' as const, render: (v: number | null) => fmt(v, 0) },
    {
      title: '損益',
      dataIndex: 'pnl',
      align: 'right' as const,
      render: (v: number | null, r: PortfolioItem) => v !== null ? (
        <span style={{ color: v > 0 ? '#ef5350' : v < 0 ? '#26a69a' : '#fff' }}>
          {fmt(v, 0)} ({fmt(r.pnl_pct)}%)
        </span>
      ) : '-',
    },
    { title: '配当利回り', dataIndex: 'dividend_yield_cost', align: 'right' as const, render: (v: number | null) => v ? `${fmt(v)}%` : '-' },
    { title: '構成比', dataIndex: 'allocation_pct', align: 'right' as const, render: (v: number | null) => v ? `${fmt(v)}%` : '-' },
    {
      title: '',
      key: 'action',
      width: 50,
      render: (_: unknown, record: PortfolioItem) => (
        <Popconfirm title="削除しますか？" onConfirm={() => onDelete(record.id)}>
          <Button type="text" danger icon={<DeleteOutlined />} size="small" />
        </Popconfirm>
      ),
    },
  ];

  return (
    <Table columns={columns} dataSource={items} rowKey="id" loading={loading} size="small" scroll={{ x: 1100 }} pagination={false} />
  );
}
