import { useState, useCallback } from 'react';
import { AutoComplete, Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { searchStocks } from '../../api/client';

interface StockOption {
  code: string;
  name: string;
  market_segment: string | null;
  sector_33: string | null;
}

interface Props {
  onSelect: (code: string) => void;
  placeholder?: string;
  style?: React.CSSProperties;
}

export default function StockSearch({ onSelect, placeholder = '銘柄コードまたは名称で検索...', style }: Props) {
  const [options, setOptions] = useState<{ value: string; label: React.ReactNode }[]>([]);
  const [timer, setTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const handleSearch = useCallback((value: string) => {
    if (timer) clearTimeout(timer);
    if (!value || value.length < 1) {
      setOptions([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const results: StockOption[] = await searchStocks(value);
        setOptions(
          results.map((s) => ({
            value: s.code,
            label: (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span><strong>{s.code}</strong> {s.name}</span>
                <span style={{ color: '#888', fontSize: 12 }}>{s.market_segment}</span>
              </div>
            ),
          }))
        );
      } catch {
        setOptions([]);
      }
    }, 300);
    setTimer(t);
  }, [timer]);

  return (
    <AutoComplete
      options={options}
      onSearch={handleSearch}
      onSelect={(value) => onSelect(value)}
      style={{ width: 320, ...style }}
    >
      <Input prefix={<SearchOutlined />} placeholder={placeholder} />
    </AutoComplete>
  );
}
