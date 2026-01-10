import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Terminal, Send, RefreshCw, Trash2 } from 'lucide-react';

import { serversAPI } from '@/api/servers';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { GlassInput } from '@/components/common/GlassInput';

interface ConsoleTabProps {
  serverId: string;
  serverStatus: string;
  canCommand?: boolean;
}

export const ConsoleTab: React.FC<ConsoleTabProps> = ({
  serverId,
  serverStatus,
  canCommand = false,
}) => {
  const { t } = useTranslation();
  const [command, setCommand] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Fetch server logs
  const { data: logs, isLoading, refetch } = useQuery({
    queryKey: ['server-logs', serverId],
    queryFn: () => serversAPI.getLogs(serverId),
    enabled: !!serverId,
    refetchInterval: serverStatus === 'running' ? 3000 : false, // Auto-refresh every 3 seconds if running
  });

  // Send command mutation
  const sendCommandMutation = useMutation({
    mutationFn: (cmd: string) => serversAPI.sendCommand(serverId, cmd),
    onSuccess: () => {
      setCommand('');
      // Refresh logs after sending command
      setTimeout(() => refetch(), 500);
    },
  });

  const handleSendCommand = () => {
    if (!command.trim() || serverStatus !== 'running') return;

    // Add to history
    setCommandHistory(prev => [...prev, command]);
    setHistoryIndex(-1);

    // Send command
    sendCommandMutation.mutate(command);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendCommand();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const newIndex = historyIndex === -1 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIndex);
        setCommand(commandHistory[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex >= 0) {
        const newIndex = historyIndex + 1;
        if (newIndex >= commandHistory.length) {
          setHistoryIndex(-1);
          setCommand('');
        } else {
          setHistoryIndex(newIndex);
          setCommand(commandHistory[newIndex]);
        }
      }
    }
  };

  // Auto-scroll to bottom when logs update
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="space-y-4">
      {/* Console Output */}
      <GlassCard>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold">{t('console.title')}</h3>
          </div>
          <div className="flex gap-2">
            <GlassButton
              size="sm"
              variant="ghost"
              onClick={() => refetch()}
              loading={isLoading}
              disabled={!serverId}
            >
              <RefreshCw className="w-4 h-4" />
            </GlassButton>
            {commandHistory.length > 0 && (
              <GlassButton
                size="sm"
                variant="ghost"
                onClick={() => {
                  setCommandHistory([]);
                  setHistoryIndex(-1);
                }}
                title={t('console.clearHistory')}
              >
                <Trash2 className="w-4 h-4" />
              </GlassButton>
            )}
          </div>
        </div>

        {/* Logs Display */}
        <div className="bg-black/40 rounded-lg p-4 font-mono text-xs">
          {isLoading ? (
            <div className="text-center py-6">
              <div className="animate-spin w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
            </div>
          ) : logs ? (
            <div className="max-h-96 overflow-y-auto custom-scrollbar">
              <pre className="text-green-400 whitespace-pre-wrap">{logs}</pre>
              <div ref={logsEndRef} />
            </div>
          ) : (
            <p className="text-white/60 text-center py-4">{t('console.noLogs')}</p>
          )}
        </div>
      </GlassCard>

      {/* Command Input */}
      <GlassCard>
        <div className="space-y-3">
          <div className="flex items-center gap-2 mb-2">
            <Terminal className="w-4 h-4 text-blue-400" />
            <h4 className="font-semibold text-sm">{t('console.sendCommand')}</h4>
          </div>

          {serverStatus !== 'running' ? (
            <div className="text-center py-4 text-white/60">
              {t('console.serverMustBeRunning')}
            </div>
          ) : !canCommand ? (
            <div className="text-center py-4 text-white/60">
              You don't have permission to send commands.
            </div>
          ) : (
            <>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-green-400 font-mono">
                    &gt;
                  </span>
                  <GlassInput
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={t('console.placeholder')}
                    className="pl-8 font-mono"
                    disabled={sendCommandMutation.isPending}
                  />
                </div>
                <GlassButton
                  onClick={handleSendCommand}
                  loading={sendCommandMutation.isPending}
                  disabled={!command.trim() || sendCommandMutation.isPending}
                  variant="primary"
                >
                  <Send className="w-4 h-4 mr-2" />
                  {t('console.send')}
                </GlassButton>
              </div>

              {/* Command hints */}
              <div className="text-xs text-white/50">
                <p className="mb-1">{t('console.commonCommands')}</p>
                <div className="flex flex-wrap gap-2">
                  {['list', 'say Hello', 'time set day', 'weather clear', 'gamemode creative @a'].map((cmd) => (
                    <button
                      key={cmd}
                      onClick={() => setCommand(cmd)}
                      className="px-2 py-1 rounded bg-white/5 hover:bg-white/10 transition-colors font-mono"
                    >
                      {cmd}
                    </button>
                  ))}
                </div>
                <p className="mt-2 text-white/40">
                  {t('console.commandHints')}
                </p>
              </div>
            </>
          )}
        </div>
      </GlassCard>
    </div>
  );
};
