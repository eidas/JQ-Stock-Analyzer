import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, LineSeries, AreaSeries, HistogramSeries } from 'lightweight-charts';
import type { IChartApi } from 'lightweight-charts';
import { Radio, Space } from 'antd';
import type { Quote } from '../../types';

interface Props {
  data: Quote[];
  height?: number;
  overlays?: Record<string, { params?: Record<string, unknown>; data?: Record<string, unknown>[] }>;
}

type ChartType = 'candlestick' | 'line' | 'area';

const SMA_COLORS = ['#2196F3', '#FF9800', '#E91E63'];

export default function PriceChart({ data, height = 400, overlays }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [chartType, setChartType] = useState<ChartType>('candlestick');

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    if (chartRef.current) {
      chartRef.current.remove();
    }

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a2e' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: '#2B2B43' },
      timeScale: {
        borderColor: '#2B2B43',
        timeVisible: false,
      },
    });

    chartRef.current = chart;

    const formattedData = data
      .filter(d => d.close !== null)
      .map(d => ({
        time: d.date,
        open: d.open || d.close!,
        high: d.high || d.close!,
        low: d.low || d.close!,
        close: d.close!,
      }))
      .sort((a, b) => a.time.localeCompare(b.time));

    if (chartType === 'candlestick') {
      const series = chart.addSeries(CandlestickSeries, {
        upColor: '#ef5350',
        downColor: '#26a69a',
        borderUpColor: '#ef5350',
        borderDownColor: '#26a69a',
        wickUpColor: '#ef5350',
        wickDownColor: '#26a69a',
      });
      series.setData(formattedData as any);
    } else if (chartType === 'line') {
      const series = chart.addSeries(LineSeries, {
        color: '#2196F3',
        lineWidth: 2,
      });
      series.setData(formattedData.map(d => ({ time: d.time, value: d.close })) as any);
    } else {
      const series = chart.addSeries(AreaSeries, {
        topColor: 'rgba(33, 150, 243, 0.4)',
        bottomColor: 'rgba(33, 150, 243, 0.0)',
        lineColor: '#2196F3',
        lineWidth: 2,
      });
      series.setData(formattedData.map(d => ({ time: d.time, value: d.close })) as any);
    }

    // Volume
    const volumeData = data
      .filter(d => d.volume !== null && d.close !== null && d.open !== null)
      .map(d => ({
        time: d.date,
        value: d.volume!,
        color: (d.close! >= d.open!) ? 'rgba(239, 83, 80, 0.3)' : 'rgba(38, 166, 154, 0.3)',
      }))
      .sort((a, b) => (a.time as string).localeCompare(b.time as string));

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeries.setData(volumeData as any);

    // SMA overlays
    if (overlays?.sma && Array.isArray(overlays.sma.data)) {
      const smaData = overlays.sma.data;
      const keys = Object.keys(smaData[0] || {}).filter(k => k.startsWith('sma_'));
      keys.forEach((key, i) => {
        const series = chart.addSeries(LineSeries, {
          color: SMA_COLORS[i % SMA_COLORS.length],
          lineWidth: 1,
          lastValueVisible: false,
          priceLineVisible: false,
        });
        series.setData(
          smaData
            .filter(d => d[key] !== null && d[key] !== undefined)
            .map(d => ({ time: d.date as string, value: d[key] as number })) as any
        );
      });
    }

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    chart.timeScale().fitContent();

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [data, chartType, height, overlays]);

  return (
    <div>
      <Space style={{ marginBottom: 8 }}>
        <Radio.Group value={chartType} onChange={e => setChartType(e.target.value)} size="small">
          <Radio.Button value="candlestick">ローソク足</Radio.Button>
          <Radio.Button value="line">ライン</Radio.Button>
          <Radio.Button value="area">エリア</Radio.Button>
        </Radio.Group>
      </Space>
      <div ref={containerRef} />
    </div>
  );
}
