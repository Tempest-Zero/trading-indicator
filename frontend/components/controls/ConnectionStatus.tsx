'use client';

import { memo } from 'react';
import { Wifi, WifiOff, Loader } from 'lucide-react';
import type { ConnectionStatus as StatusType } from '@/hooks';

interface ConnectionStatusProps {
  status: StatusType;
  lastUpdate?: Date | null;
}

function ConnectionStatusComponent({ status, lastUpdate }: ConnectionStatusProps) {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          color: 'text-green-400',
          bgColor: 'bg-green-400',
          label: 'Connected',
        };
      case 'connecting':
        return {
          icon: Loader,
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-400',
          label: 'Connecting...',
          animate: true,
        };
      case 'error':
        return {
          icon: WifiOff,
          color: 'text-red-400',
          bgColor: 'bg-red-400',
          label: 'Error',
        };
      default:
        return {
          icon: WifiOff,
          color: 'text-slate-400',
          bgColor: 'bg-slate-400',
          label: 'Disconnected',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-3 text-sm">
      {/* Last update timestamp */}
      {lastUpdate && (
        <div className="text-slate-500">
          Updated: <span className="text-slate-400">{formatTime(lastUpdate)}</span>
        </div>
      )}

      {/* Status indicator */}
      <div className="flex items-center gap-2">
        <div className="relative">
          <div className={`h-2 w-2 rounded-full ${config.bgColor}`}>
            {status === 'connected' && (
              <div className={`absolute inset-0 h-2 w-2 rounded-full ${config.bgColor} animate-ping`} />
            )}
          </div>
        </div>
        <Icon
          className={`h-4 w-4 ${config.color} ${config.animate ? 'animate-spin' : ''}`}
        />
        <span className={config.color}>{config.label}</span>
      </div>
    </div>
  );
}

export const ConnectionStatus = memo(ConnectionStatusComponent);
