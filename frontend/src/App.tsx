import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, Layout, Menu, theme as antTheme } from 'antd';
import {
  DashboardOutlined,
  SearchOutlined,
  LineChartOutlined,
  FundOutlined,
  CalculatorOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import SyncStatus from './components/common/SyncStatus';
import Dashboard from './pages/Dashboard';
import Screening from './pages/Screening';
import StockDetail from './pages/StockDetail';
import Portfolio from './pages/Portfolio';
import CustomAnalysis from './pages/CustomAnalysis';
import Settings from './pages/Settings';

const { Sider, Header, Content, Footer } = Layout;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

const MENU_ITEMS = [
  { key: '/', icon: <DashboardOutlined />, label: 'ダッシュボード' },
  { key: '/screening', icon: <SearchOutlined />, label: 'スクリーニング' },
  { key: '/stocks', icon: <LineChartOutlined />, label: '個別銘柄' },
  { key: '/portfolio', icon: <FundOutlined />, label: 'ポートフォリオ' },
  { key: '/custom', icon: <CalculatorOutlined />, label: 'カスタム計算' },
  { key: '/settings', icon: <SettingOutlined />, label: '設定' },
];

function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = MENU_ITEMS.find(item =>
    item.key !== '/' ? location.pathname.startsWith(item.key) : location.pathname === '/'
  )?.key || '/';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        breakpoint="lg"
        collapsedWidth="64"
        style={{ background: '#141414' }}
      >
        <div style={{ padding: '16px 16px 8px', color: '#fff', fontWeight: 'bold', fontSize: 14, textAlign: 'center' }}>
          JQ Stock Analyzer
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={MENU_ITEMS}
          onClick={({ key }) => navigate(key)}
          style={{ background: '#141414' }}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#1a1a2e',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          borderBottom: '1px solid #303030',
        }}>
          <SyncStatus />
        </Header>
        <Content style={{ margin: 16, padding: 24, background: '#0d0d1a', borderRadius: 8, minHeight: 360 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/screening" element={<Screening />} />
            <Route path="/stocks/:code" element={<StockDetail />} />
            <Route path="/stocks" element={<Screening />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/custom" element={<CustomAnalysis />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Content>
        <Footer style={{ textAlign: 'center', background: '#141414', color: '#555' }}>
          JQ Stock Analyzer v0.1.0
        </Footer>
      </Layout>
    </Layout>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          algorithm: antTheme.darkAlgorithm,
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
          },
        }}
      >
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  );
}
