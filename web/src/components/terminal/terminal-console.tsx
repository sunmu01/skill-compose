'use client';

import { useRef, useEffect, useCallback, useState } from 'react';
import { useTranslation } from '@/i18n/client';
import { BACKEND_API_BASE } from '@/lib/api';
import '@xterm/xterm/css/xterm.css';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

function getWsUrl(cols: number, rows: number): string {
  // BACKEND_API_BASE is like http://localhost:62610/api/v1
  const base = BACKEND_API_BASE.replace(/^http/, 'ws');
  return `${base}/terminal/ws?cols=${cols}&rows=${rows}`;
}

export function TerminalConsole() {
  const { t } = useTranslation('terminal');
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<any>(null);
  const fitAddonRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(async () => {
    if (!containerRef.current || !mountedRef.current) return;

    // Dynamic import for SSR safety
    const [
      { Terminal },
      { FitAddon },
      { WebLinksAddon },
    ] = await Promise.all([
      import('@xterm/xterm'),
      import('@xterm/addon-fit'),
      import('@xterm/addon-web-links'),
    ]);

    // Clean up previous terminal and WebSocket
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    if (termRef.current) {
      termRef.current.dispose();
      termRef.current = null;
    }
    // Clear container DOM to avoid stacking
    if (containerRef.current) {
      containerRef.current.innerHTML = '';
    }

    const fitAddon = new FitAddon();
    fitAddonRef.current = fitAddon;

    const terminal = new Terminal({
      cursorBlink: true,
      cursorStyle: 'block',
      fontSize: 14,
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, Monaco, 'Courier New', monospace",
      theme: {
        background: '#09090b', // zinc-950
        foreground: '#fafafa', // zinc-50
        cursor: '#22c55e',     // green-500
        selectionBackground: '#3f3f46', // zinc-700
        black: '#18181b',
        red: '#ef4444',
        green: '#22c55e',
        yellow: '#eab308',
        blue: '#3b82f6',
        magenta: '#a855f7',
        cyan: '#06b6d4',
        white: '#fafafa',
        brightBlack: '#71717a',
        brightRed: '#f87171',
        brightGreen: '#4ade80',
        brightYellow: '#facc15',
        brightBlue: '#60a5fa',
        brightMagenta: '#c084fc',
        brightCyan: '#22d3ee',
        brightWhite: '#ffffff',
      },
      scrollback: 10000,
      convertEol: true,
    });

    terminal.loadAddon(fitAddon);
    terminal.loadAddon(new WebLinksAddon());
    terminal.open(containerRef.current);
    fitAddon.fit();
    termRef.current = terminal;

    // Connect WebSocket
    setStatus('connecting');
    const ws = new WebSocket(getWsUrl(terminal.cols, terminal.rows));
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setStatus('connected');
      terminal.focus();
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'output') {
        terminal.write(msg.data);
      } else if (msg.type === 'exit') {
        terminal.writeln(`\r\n\x1b[33m[Shell exited with code ${msg.code}]\x1b[0m`);
        // Auto-reconnect after shell exit
        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current) connect();
        }, 1000);
      } else if (msg.type === 'error') {
        terminal.writeln(`\r\n\x1b[31m[Error: ${msg.data}]\x1b[0m`);
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setStatus('disconnected');
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setStatus('disconnected');
    };

    // Send keystrokes to WebSocket
    terminal.onData((data: string) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'input', data }));
      }
    });

    // Send resize events
    terminal.onResize(({ cols, rows }: { cols: number; rows: number }) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols, rows }));
      }
    });
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    // ResizeObserver for auto-fit
    const container = containerRef.current;
    let resizeObserver: ResizeObserver | null = null;
    if (container) {
      resizeObserver = new ResizeObserver(() => {
        if (fitAddonRef.current && termRef.current) {
          try {
            fitAddonRef.current.fit();
          } catch {
            // Terminal may not be fully initialized
          }
        }
      });
      resizeObserver.observe(container);
    }

    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      resizeObserver?.disconnect();
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
      if (termRef.current) {
        termRef.current.dispose();
        termRef.current = null;
      }
    };
  }, [connect]);

  const statusColor = status === 'connected'
    ? 'bg-green-500'
    : status === 'connecting'
      ? 'bg-yellow-500'
      : 'bg-red-500';

  const statusText = t(`status.${status}`);

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex items-center gap-2 mb-2">
        <span className={`inline-block w-2 h-2 rounded-full ${statusColor}`} />
        <span className="text-sm text-muted-foreground">{statusText}</span>
      </div>
      <div
        ref={containerRef}
        className="flex-1 rounded-lg border bg-zinc-950 overflow-hidden"
      />
    </div>
  );
}
