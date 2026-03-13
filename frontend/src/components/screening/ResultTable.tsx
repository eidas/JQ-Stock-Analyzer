import { Table } from 'antd';
import { useNavigate } from 'react-router-dom';
import type { ScreeningResult } from '../../types';

interface Props {
  results: ScreeningResult[];
  total: number;
  page: number;
  perPage: number;
  loading: boolean;
  onPageChange: (page: number) => void;
  onSortChange: (field: string, order: string) => void;
}

const formatNumber = (v: number | null, decimals = 2) =>
  v !== null && v !== undefined ? v.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) : '-';

const formatMarketCap = (v: number | null) => {
  if (!v) return '-';
  if (v >= 1e12) return `${(v / 1e12).toFixed(1)}兆`;
  if (v >= 1e8) return `${(v / 1e8).toFixed(0)}億`;
  return v.toLocaleString();
};

export default function ResultTable({ results, total, page, perPage, loading, onPageChange, onSortChange }: Props) {
  const navigate = useNavigate();

  const columns = [
    {
      title: 'コード',
      dataIndex: 'code',
      key: 'code',
      sorter: true,
      render: (code: string) => (
        <a onClick={() => navigate(`/stocks/${code}`)}>{code}</a>
      ),
    },
    { title: '銘柄名', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '市場', dataIndex: 'market_segment', key: 'market_segment', width: 100 },
    { title: '業種', dataIndex: 'sector_33', key: 'sector_33', width: 120, ellipsis: true },
    {
      title: '終値',
      dataIndex: 'close',
      key: 'close',
      sorter: true,
      align: 'right' as const,
      render: (v: number | null) => formatNumber(v, 1),
    },
    {
      title: '前日比(%)',
      dataIndex: 'change_pct',
      key: 'change_pct',
      align: 'right' as const,
      render: (v: number | null) => v !== null ? (
        <span style={{ color: v > 0 ? '#ef5350' : v < 0 ? '#26a69a' : '#fff' }}>
          {v > 0 ? '+' : ''}{formatNumber(v)}%
        </span>
      ) : '-',
    },
    { title: 'PER', dataIndex: 'per', key: 'per', sorter: true, align: 'right' as const, render: (v: number | null) => formatNumber(v, 1) },
    { title: 'PBR', dataIndex: 'pbr', key: 'pbr', sorter: true, align: 'right' as const, render: (v: number | null) => formatNumber(v) },
    { title: 'ROE(%)', dataIndex: 'roe', key: 'roe', sorter: true, align: 'right' as const, render: (v: number | null) => formatNumber(v, 1) },
    { title: '配当(%)', dataIndex: 'dividend_yield', key: 'dividend_yield', sorter: true, align: 'right' as const, render: (v: number | null) => formatNumber(v) },
    { title: '回転日数', dataIndex: 'turnover_days_20', key: 'turnover_days_20', sorter: true, align: 'right' as const, render: (v: number | null) => formatNumber(v, 1) },
    { title: '時価総額', dataIndex: 'market_cap', key: 'market_cap', sorter: true, align: 'right' as const, render: (v: number | null) => formatMarketCap(v) },
  ];

  return (
    <Table
      columns={columns}
      dataSource={results}
      rowKey="code"
      loading={loading}
      pagination={{
        current: page,
        pageSize: perPage,
        total,
        onChange: onPageChange,
        showTotal: (t) => `全 ${t} 件`,
      }}
      onChange={(_pagination, _filters, sorter: any) => {
        if (sorter?.field) {
          onSortChange(sorter.field, sorter.order === 'descend' ? 'desc' : 'asc');
        }
      }}
      size="small"
      scroll={{ x: 1200 }}
    />
  );
}
