import { Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from 'recharts';
import { Tabs } from 'antd';
import type { FinancialStatement } from '../../types';

interface Props {
  data: FinancialStatement[];
}

const formatBillion = (v: number) => `${(v / 1_000_000_000).toFixed(1)}B`;
const formatNumber = (v: number | null | undefined) => v?.toLocaleString() ?? '-';

export default function FinancialChart({ data }: Props) {
  // Sort by fiscal year ascending, take annual results
  const sorted = [...data]
    .sort((a, b) => (a.fiscal_year || '').localeCompare(b.fiscal_year || ''));

  const earningsData = sorted.map(d => ({
    period: `${d.fiscal_year} ${d.type_of_document || ''}`.trim(),
    net_sales: d.net_sales,
    operating_profit: d.operating_profit,
    net_income: d.net_income,
  }));

  const perShareData = sorted.map(d => ({
    period: `${d.fiscal_year} ${d.type_of_document || ''}`.trim(),
    eps: d.eps,
    bps: d.bps,
    dividend: d.dividend_forecast,
  }));

  const ratioData = sorted.map(d => ({
    period: `${d.fiscal_year} ${d.type_of_document || ''}`.trim(),
    operating_margin: d.net_sales && d.operating_profit ? (d.operating_profit / d.net_sales * 100) : null,
    equity_ratio: d.equity_ratio,
  }));

  return (
    <Tabs items={[
      {
        key: 'earnings',
        label: '業績推移',
        children: (
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={earningsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="period" tick={{ fill: '#aaa', fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
              <YAxis tickFormatter={formatBillion} tick={{ fill: '#aaa' }} />
              <Tooltip formatter={(v) => formatNumber(v as number)} />
              <Legend />
              <Bar dataKey="net_sales" name="売上高" fill="#8884d8" opacity={0.7} />
              <Bar dataKey="operating_profit" name="営業利益" fill="#82ca9d" />
              <Line type="monotone" dataKey="net_income" name="純利益" stroke="#ffc658" strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
        ),
      },
      {
        key: 'pershare',
        label: 'EPS/BPS/配当',
        children: (
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={perShareData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="period" tick={{ fill: '#aaa', fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
              <YAxis tick={{ fill: '#aaa' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="eps" name="EPS" fill="#8884d8" />
              <Line type="monotone" dataKey="bps" name="BPS" stroke="#82ca9d" strokeWidth={2} />
              <Line type="monotone" dataKey="dividend" name="配当" stroke="#ffc658" strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
        ),
      },
      {
        key: 'ratios',
        label: '財務比率',
        children: (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={ratioData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="period" tick={{ fill: '#aaa', fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
              <YAxis tick={{ fill: '#aaa' }} unit="%" />
              <Tooltip formatter={(v) => `${(v as number)?.toFixed(1)}%`} />
              <Legend />
              <Line type="monotone" dataKey="operating_margin" name="営業利益率" stroke="#8884d8" strokeWidth={2} />
              <Line type="monotone" dataKey="equity_ratio" name="自己資本比率" stroke="#82ca9d" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        ),
      },
    ]} />
  );
}
