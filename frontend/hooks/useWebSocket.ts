// WebSocket hook for real-time updates

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from './useAnalysis';
import type { FullAnalysis, WSMessage } from '@/types';

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface UseWebSocketOptions {
  clientId: string;
  onMessage?: (data: FullAnalysis) => void;
  onError?: (error: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    clientId,
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    autoReconnect = true,
    reconnectInterval = 5000,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const subscribedSymbolsRef = useRef<Set<string>>(new Set());
  const queryClient = useQueryClient();

  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');
    const ws = new WebSocket(`${WS_BASE}/ws/${clientId}`);

    ws.onopen = () => {
      setStatus('connected');
      onConnect?.();

      // Resubscribe to symbols
      subscribedSymbolsRef.current.forEach((symbol) => {
        ws.send(JSON.stringify({ action: 'subscribe', symbols: [symbol] }));
      });
    };

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);

        if (message.type === 'analysis' && message.data) {
          setLastUpdate(new Date());
          onMessage?.(message.data);

          // Update React Query cache
          const analysis = message.data;
          queryClient.setQueryData(
            queryKeys.analysis(analysis.symbol, '1h'),
            analysis
          );
        } else if (message.type === 'error' && message.message) {
          onError?.(message.message);
        }
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };

    ws.onerror = () => {
      setStatus('error');
      onError?.('WebSocket connection error');
    };

    ws.onclose = () => {
      setStatus('disconnected');
      onDisconnect?.();

      // Auto reconnect
      if (autoReconnect) {
        reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
      }
    };

    wsRef.current = ws;
  }, [clientId, onMessage, onError, onConnect, onDisconnect, autoReconnect, reconnectInterval, queryClient]);

  // Disconnect
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Subscribe to symbols
  const subscribe = useCallback((symbols: string[]) => {
    symbols.forEach((s) => subscribedSymbolsRef.current.add(s));

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'subscribe', symbols }));
    }
  }, []);

  // Unsubscribe from symbols
  const unsubscribe = useCallback((symbols: string[]) => {
    symbols.forEach((s) => subscribedSymbolsRef.current.delete(s));

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'unsubscribe', symbols }));
    }
  }, []);

  // Request analysis
  const requestAnalysis = useCallback((symbol: string, timeframe: string = '1h') => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'analyze', symbol, timeframe }));
    }
  }, []);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    status,
    lastUpdate,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    requestAnalysis,
    isConnected: status === 'connected',
  };
}
