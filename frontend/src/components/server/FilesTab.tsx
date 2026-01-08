import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
  Folder,
  File,
  FileText,
  FileCode,
  FileJson,
  Download,
  Trash2,
  Edit,
  Upload,
  ChevronRight,
  Home,
  X,
  Save,
} from 'lucide-react';

import { filesAPI, FileItem } from '@/api/files';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { formatBytes, formatRelativeTime } from '@/utils/formatters';

interface FilesTabProps {
  serverId: string;
}

export const FilesTab: React.FC<FilesTabProps> = ({ serverId }) => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [currentPath, setCurrentPath] = useState('');
  const [editingFile, setEditingFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Fetch directory listing
  const { data: listing, isLoading } = useQuery({
    queryKey: ['server-files', serverId, currentPath],
    queryFn: () => filesAPI.listFiles(serverId, currentPath),
  });

  // Fetch file content for editing
  const { data: fileData, isLoading: isLoadingFile } = useQuery({
    queryKey: ['file-content', serverId, editingFile],
    queryFn: () => filesAPI.readFile(serverId, editingFile!),
    enabled: !!editingFile,
  });

  // Update file content when data is fetched
  React.useEffect(() => {
    if (fileData) {
      setFileContent(fileData.content);
    }
  }, [fileData]);

  // Save file mutation
  const saveMutation = useMutation({
    mutationFn: () => filesAPI.writeFile(serverId, editingFile!, fileContent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-files', serverId] });
      setEditingFile(null);
      setFileContent('');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (path: string) => filesAPI.deleteFile(serverId, path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-files', serverId, currentPath] });
    },
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => filesAPI.uploadFile(serverId, file, currentPath),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-files', serverId, currentPath] });
      setUploadFile(null);
    },
  });

  const getFileIcon = (item: FileItem) => {
    if (item.type === 'directory') {
      return <Folder className="w-5 h-5 text-blue-400" />;
    }

    const ext = item.extension?.toLowerCase();
    if (['json', 'yml', 'yaml'].includes(ext || '')) {
      return <FileJson className="w-5 h-5 text-green-400" />;
    }
    if (['properties', 'txt', 'log'].includes(ext || '')) {
      return <FileText className="w-5 h-5 text-gray-400" />;
    }
    if (['js', 'ts', 'java', 'py'].includes(ext || '')) {
      return <FileCode className="w-5 h-5 text-purple-400" />;
    }
    return <File className="w-5 h-5 text-white/60" />;
  };

  const handleItemClick = (item: FileItem) => {
    if (item.type === 'directory') {
      setCurrentPath(item.path);
    } else {
      setEditingFile(item.path);
    }
  };

  const handleDelete = (item: FileItem) => {
    if (window.confirm(t('files.deleteConfirm', { name: item.name }))) {
      deleteMutation.mutate(item.path);
    }
  };

  const handleUpload = () => {
    if (uploadFile) {
      uploadMutation.mutate(uploadFile);
    }
  };

  const navigateToPath = (path: string) => {
    setCurrentPath(path);
  };

  // Breadcrumb navigation
  const pathParts = currentPath ? currentPath.split('/') : [];
  const breadcrumbs = [
    { name: t('common.back'), path: '' },
    ...pathParts.map((part, index) => ({
      name: part,
      path: pathParts.slice(0, index + 1).join('/'),
    })),
  ];

  return (
    <div className="space-y-4">
      {/* File Editor Modal */}
      {editingFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-4xl max-h-[90vh] overflow-hidden">
            <GlassCard>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{editingFile}</h3>
                <button
                  onClick={() => {
                    setEditingFile(null);
                    setFileContent('');
                  }}
                  className="text-white/60 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {isLoadingFile ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
                </div>
              ) : (
                <>
                  <textarea
                    value={fileContent}
                    onChange={(e) => setFileContent(e.target.value)}
                    className="w-full h-96 px-4 py-3 rounded-lg bg-black/40 border border-white/20 text-white font-mono text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 outline-none resize-none"
                    spellCheck={false}
                  />

                  <div className="flex gap-2 mt-4">
                    <GlassButton
                      variant="primary"
                      onClick={() => saveMutation.mutate()}
                      loading={saveMutation.isPending}
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {t('files.saveChanges')}
                    </GlassButton>
                    <GlassButton
                      variant="ghost"
                      onClick={() => {
                        setEditingFile(null);
                        setFileContent('');
                      }}
                    >
                      {t('common.cancel')}
                    </GlassButton>
                  </div>
                </>
              )}
            </GlassCard>
          </div>
        </div>
      )}

      {/* Upload Section */}
      <GlassCard>
        <h3 className="text-lg font-semibold mb-4">{t('files.uploadFile')}</h3>
        <div className="flex gap-2">
          <input
            type="file"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            className="flex-1 text-sm text-white/70"
          />
          <GlassButton
            variant="primary"
            onClick={handleUpload}
            disabled={!uploadFile}
            loading={uploadMutation.isPending}
          >
            <Upload className="w-4 h-4 mr-2" />
            {t('common.upload')}
          </GlassButton>
        </div>
      </GlassCard>

      {/* File Browser */}
      <GlassCard>
        <div className="space-y-4">
          {/* Breadcrumb Navigation */}
          <div className="flex items-center gap-2 text-sm flex-wrap">
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={crumb.path}>
                {index > 0 && <ChevronRight className="w-4 h-4 text-white/40" />}
                <button
                  onClick={() => navigateToPath(crumb.path)}
                  className={`flex items-center gap-1 hover:text-blue-400 transition-colors ${
                    index === breadcrumbs.length - 1 ? 'text-white font-semibold' : 'text-white/60'
                  }`}
                >
                  {index === 0 && <Home className="w-4 h-4" />}
                  {crumb.name}
                </button>
              </React.Fragment>
            ))}
          </div>

          {/* File Listing */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
            </div>
          ) : listing && listing.items.length > 0 ? (
            <div className="space-y-1">
              {listing.items.map((item) => (
                <div
                  key={item.path}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors group"
                >
                  <button
                    onClick={() => handleItemClick(item)}
                    className="flex items-center gap-3 flex-1 text-left"
                  >
                    {getFileIcon(item)}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{item.name}</p>
                      <p className="text-xs text-white/50">
                        {item.type === 'file' && `${formatBytes(item.size)} • `}
                        {formatRelativeTime(new Date(item.modified * 1000).toISOString())}
                      </p>
                    </div>
                  </button>

                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {item.type === 'file' && (
                      <>
                        <button
                          onClick={() => setEditingFile(item.path)}
                          className="p-2 rounded hover:bg-white/10 text-white/60 hover:text-white transition-colors"
                          title={t('files.edit')}
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <a
                          href={filesAPI.downloadFile(serverId, item.path)}
                          download={item.name}
                          className="p-2 rounded hover:bg-white/10 text-white/60 hover:text-white transition-colors"
                          title={t('files.download')}
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      </>
                    )}
                    <button
                      onClick={() => handleDelete(item)}
                      className="p-2 rounded hover:bg-white/10 text-red-400 hover:text-red-300 transition-colors"
                      title={t('files.delete')}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Folder className="w-16 h-16 text-white/20 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('files.emptyDirectory')}</h3>
              <p className="text-white/60">{t('files.emptyDirectoryDesc')}</p>
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  );
};
