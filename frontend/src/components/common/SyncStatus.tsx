import { useQuery } from '@tanstack/react-query';
import { Button, Progress, Tooltip, notification } from 'antd';
import { SyncOutlined, CloudSyncOutlined } from '@ant-design/icons';
import { useEffect, useRef } from 'react';
import { getSyncStatus, syncAll } from '../../api/client';

export default function SyncStatus() {
  const prevStatus = useRef<string>('');
  const { data: status } = useQuery({
    queryKey: ['syncStatus'],
    queryFn: getSyncStatus,
    refetchInterval: 5000,
  });

  useEffect(() => {
    if (!status) return;
    if (prevStatus.current === 'running' && status.status === 'success') {
      notification.success({ message: '同期完了', description: status.current_step });
    } else if (prevStatus.current === 'running' && status.status === 'error') {
      notification.error({ message: '同期エラー', description: status.error_message || '不明なエラー' });
    }
    prevStatus.current = status.status;
  }, [status]);

  const handleSync = () => {
    syncAll();
    notification.info({ message: 'データ同期を開始しました' });
  };

  const isRunning = status?.status === 'running';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      {isRunning && (
        <Tooltip title={status?.current_step}>
          <Progress
            type="circle"
            percent={Math.round(status?.progress_pct || 0)}
            size={28}
            strokeWidth={8}
          />
        </Tooltip>
      )}
      <Tooltip title={status?.completed_at ? `最終同期: ${status.completed_at}` : '未同期'}>
        <Button
          type="text"
          icon={isRunning ? <SyncOutlined spin /> : <CloudSyncOutlined />}
          onClick={handleSync}
          disabled={isRunning}
        >
          データ同期
        </Button>
      </Tooltip>
    </div>
  );
}
