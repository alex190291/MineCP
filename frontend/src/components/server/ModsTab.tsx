import React, { useState, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Upload, Download, Trash2, Search, Package, ExternalLink } from 'lucide-react';

import { modsAPI } from '@/api/mods';
import { serversAPI } from '@/api/servers';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { GlassInput } from '@/components/common/GlassInput';
import { formatBytes, formatRelativeTime } from '@/utils/formatters';
import type { ModSearchResult } from '@/api/mods';

interface ModsTabProps {
  serverId: string;
}

const getModNameFromUrl = (url: string) => {
  const cleaned = url.split('?')[0].replace(/\/+$/, '');
  const parts = cleaned.split('/').filter(Boolean);
  let lastPart = parts[parts.length - 1] || 'mod';

  if (lastPart === 'download' && parts.length > 1) {
    lastPart = parts[parts.length - 2];
  }

  const name = lastPart.replace(/\.jar$/i, '');
  return name || 'mod';
};

const getModSourceFromUrl = (url: string) => {
  const lowered = url.toLowerCase();
  if (lowered.includes('modrinth.com')) {
    return 'modrinth';
  }
  if (lowered.includes('spigotmc.org')) {
    return 'spigotmc';
  }
  return 'curseforge';
};

const getSearchResultUrl = (result: ModSearchResult) => {
  if (result.url) {
    return result.url;
  }

  if (result.source === 'modrinth' && result.slug) {
    const typePath = result.content_type === 'plugin' ? 'plugin' : 'mod';
    return `https://modrinth.com/${typePath}/${result.slug}`;
  }

  return '';
};

export const ModsTab: React.FC<ModsTabProps> = ({ serverId }) => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [modrinthUrl, setModrinthUrl] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadingFile, setUploadingFile] = useState(false);

  // Fetch server info to get server type
  const { data: server } = useQuery({
    queryKey: ['server', serverId],
    queryFn: () => serversAPI.getById(serverId),
  });

  const { data: mods, isLoading } = useQuery({
    queryKey: ['server-mods', serverId],
    queryFn: () => modsAPI.listServerMods(serverId),
  });

  const { data: searchResults } = useQuery({
    queryKey: ['mods-search', searchQuery, server?.type, server?.version],
    queryFn: () => modsAPI.searchMods(searchQuery, server?.version, server?.type),
    enabled: searchQuery.length > 2 && !!server,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      setUploadingFile(true);
      const uploadResult = await modsAPI.uploadMod(file);
      return modsAPI.installMod(serverId, {
        mod_name: file.name.replace('.jar', ''),
        file_path: uploadResult.file_path,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-mods', serverId] });
      setUploadingFile(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    onError: () => {
      setUploadingFile(false);
    },
  });

  const downloadModMutation = useMutation({
    mutationFn: (url: string) => {
      // Extract mod info from Modrinth/CurseForge/SpigotMC URL
      const modName = getModNameFromUrl(url);
      return modsAPI.installMod(serverId, {
        mod_name: modName,
        mod_url: url,
        source: getModSourceFromUrl(url),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-mods', serverId] });
      setModrinthUrl('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (modId: string) => modsAPI.deleteMod(serverId, modId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-mods', serverId] });
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.jar')) {
      uploadMutation.mutate(file);
    }
  };

  const handleDownloadMod = () => {
    if (modrinthUrl) {
      downloadModMutation.mutate(modrinthUrl);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <GlassCard>
        <h3 className="text-lg font-semibold mb-4">{t('mods.addMods')}</h3>

        <div className="space-y-4">
          {/* File Upload */}
          <div>
            <label className="block text-sm text-white/70 mb-2">{t('mods.uploadModFile')}</label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".jar"
              onChange={handleFileSelect}
              className="hidden"
            />
            <GlassButton
              onClick={() => fileInputRef.current?.click()}
              loading={uploadingFile}
              disabled={uploadingFile}
            >
              <Upload className="w-4 h-4 mr-2" />
              {uploadingFile ? t('mods.uploading') : t('mods.uploadFile')}
            </GlassButton>
          </div>

          {/* Download from URL */}
          <div>
            <label className="block text-sm text-white/70 mb-2">
              {t('mods.downloadFromModrinth')}
            </label>
            <div className="flex gap-2">
              <GlassInput
                placeholder={t('mods.downloadUrlPlaceholder')}
                value={modrinthUrl}
                onChange={(e) => setModrinthUrl(e.target.value)}
              />
              <GlassButton
                onClick={handleDownloadMod}
                loading={downloadModMutation.isPending}
                disabled={!modrinthUrl || downloadModMutation.isPending}
              >
                <Download className="w-4 h-4 mr-2" />
                {t('common.download')}
              </GlassButton>
            </div>
          </div>

          {/* Search Mods */}
          <div>
            <label className="block text-sm text-white/70 mb-2">{t('mods.search')}</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
              <GlassInput
                placeholder={t('mods.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {searchResults && searchResults.length > 0 && (
              <div className="mt-3 space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
                {searchResults.map((result) => {
                  const resultUrl = getSearchResultUrl(result);
                  const typeLabel =
                    result.content_type === 'plugin'
                      ? t('mods.type.plugin')
                      : t('mods.type.mod');

                  return (
                    <div
                      key={result.project_id}
                      className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors flex items-start justify-between"
                    >
                      <div className="flex-1">
                        <h4 className="font-semibold">{result.title}</h4>
                        <p className="text-xs text-white/60 mt-1 line-clamp-2">
                          {result.description}
                        </p>
                        <p className="text-xs text-white/40 mt-1">
                          {typeLabel} • {result.downloads.toLocaleString()} {t('mods.downloads')}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <GlassButton
                          size="sm"
                          variant="ghost"
                          onClick={() => window.open(resultUrl, '_blank')}
                          title={t('mods.show')}
                          disabled={!resultUrl}
                        >
                          <ExternalLink className="w-4 h-4" />
                        </GlassButton>
                        <GlassButton
                          size="sm"
                          onClick={() => setModrinthUrl(resultUrl)}
                          disabled={!resultUrl}
                        >
                          {t('mods.select')}
                        </GlassButton>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </GlassCard>

      {/* Installed Mods */}
      <GlassCard>
        <h3 className="text-lg font-semibold mb-4">{t('mods.installed')}</h3>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : mods && mods.length > 0 ? (
          <div className="space-y-2">
            {mods.map((mod) => (
              <div
                key={mod.id}
                className="p-4 rounded-lg bg-white/5 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="bg-purple-500/20 p-2 rounded-lg">
                    <Package className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h4 className="font-semibold">{mod.name}</h4>
                    <div className="flex gap-3 text-xs text-white/60 mt-1">
                      {mod.version && <span>v{mod.version}</span>}
                      <span>
                        {mod.content_type === 'plugin'
                          ? t('mods.type.plugin')
                          : t('mods.type.mod')}
                      </span>
                      <span>{mod.source}</span>
                      {mod.file_size > 0 && <span>{formatBytes(mod.file_size)}</span>}
                      <span>{formatRelativeTime(mod.created_at)}</span>
                    </div>
                  </div>
                </div>

                <GlassButton
                  size="sm"
                  variant="danger"
                  onClick={() => deleteMutation.mutate(mod.id)}
                  loading={deleteMutation.isPending}
                >
                  <Trash2 className="w-4 h-4" />
                </GlassButton>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Package className="w-16 h-16 text-white/20 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">{t('mods.noMods')}</h3>
            <p className="text-white/60">{t('mods.noModsDesc')}</p>
          </div>
        )}
      </GlassCard>
    </div>
  );
};
