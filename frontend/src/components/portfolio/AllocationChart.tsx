import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import type { PortfolioItem } from '../../types';

interface Props {
  items: PortfolioItem[];
}

const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE',
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57',
];

export default function AllocationChart({ items }: Props) {
  // Group by sector
  const sectorMap: Record<string, number> = {};
  items.forEach(item => {
    const sector = item.sector_33 || '不明';
    sectorMap[sector] = (sectorMap[sector] || 0) + (item.eval_amount || 0);
  });

  const data = Object.entries(sectorMap)
    .map(([name, value]) => ({ name, value: Math.round(value) }))
    .filter(d => d.value > 0)
    .sort((a, b) => b.value - a.value);

  if (data.length === 0) {
    return <div style={{ color: '#888', textAlign: 'center', padding: 40 }}>データなし</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(1)}%`}
        >
          {data.map((_entry, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(v) => `¥${(v as number).toLocaleString()}`} />
      </PieChart>
    </ResponsiveContainer>
  );
}
