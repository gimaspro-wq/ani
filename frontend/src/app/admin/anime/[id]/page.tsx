'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { RequireAuth } from '@/components/admin/require-auth';
import { AdminNav } from '@/components/admin/admin-nav';
import { adminAPI, type AnimeDetail, type EpisodeListItem, type VideoSourceListItem } from '@/lib/admin-api';

export default function AnimeEditPage() {
  const params = useParams();
  const router = useRouter();
  const animeId = params.id as string;

  const [anime, setAnime] = useState<AnimeDetail | null>(null);
  const [episodes, setEpisodes] = useState<EpisodeListItem[]>([]);
  const [selectedEpisodeId, setSelectedEpisodeId] = useState<string | null>(null);
  const [videoSources, setVideoSources] = useState<VideoSourceListItem[]>([]);
  const [isVideoLoading, setIsVideoLoading] = useState(false);
  const [videoError, setVideoError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [episodeForm, setEpisodeForm] = useState({
    number: '',
    title: '',
    source_episode_id: '',
    is_active: true,
  });
  const [videoCreateForm, setVideoCreateForm] = useState({
    type: 'hls',
    url: '',
    source_name: '',
    priority: '',
    is_active: true,
  });

  const reloadEpisodes = async () => {
    const episodesData = await adminAPI.listEpisodes(animeId);
    setEpisodes(episodesData.items);
  };

  const loadVideoSources = async (episodeId: string) => {
    setIsVideoLoading(true);
    setVideoError('');
    try {
      const data = await adminAPI.listVideoSources(episodeId);
      setVideoSources(data.items);
    } catch (err: any) {
      setVideoError(err.message || 'Failed to load video sources');
    } finally {
      setIsVideoLoading(false);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [animeData, episodesData] = await Promise.all([
          adminAPI.getAnime(animeId),
          adminAPI.listEpisodes(animeId),
        ]);
        setAnime(animeData);
        setEpisodes(episodesData.items);

        // Set form values
        setTitle(animeData.title);
        setDescription(animeData.description || '');
        setStatus(animeData.status || '');
        setIsActive(animeData.is_active);
      } catch (err: any) {
        setError(err.message || 'Failed to load anime');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [animeId]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError('');

    try {
      const updated = await adminAPI.updateAnime(animeId, {
        title,
         description: description || undefined,
         status: status || undefined,
         is_active: isActive,
      });
      setAnime(updated);
      alert('Anime updated successfully!');
    } catch (err: any) {
      setError(err.message || 'Failed to update anime');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateEpisode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!episodeForm.number || !episodeForm.source_episode_id) return;
    try {
      await adminAPI.createEpisode({
        anime_id: animeId,
        number: Number(episodeForm.number),
        title: episodeForm.title || undefined,
        source_episode_id: episodeForm.source_episode_id,
        is_active: episodeForm.is_active,
      });
      await reloadEpisodes();
      setEpisodeForm({ number: '', title: '', source_episode_id: '', is_active: true });
    } catch (err: any) {
      alert(err.message || 'Failed to create episode');
    }
  };

  const handleSelectEpisode = async (episodeId: string) => {
    setSelectedEpisodeId(episodeId);
    await loadVideoSources(episodeId);
  };

  const handleCreateVideo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEpisodeId) return;
    try {
      await adminAPI.createVideoSource({
        episode_id: selectedEpisodeId,
        type: videoCreateForm.type,
        url: videoCreateForm.url,
        source_name: videoCreateForm.source_name,
        priority: videoCreateForm.priority ? Number(videoCreateForm.priority) : undefined,
        is_active: videoCreateForm.is_active,
      });
      await loadVideoSources(selectedEpisodeId);
      setVideoCreateForm({ type: 'hls', url: '', source_name: '', priority: '', is_active: true });
    } catch (err: any) {
      alert(err.message || 'Failed to create video source');
    }
  };

  const handleToggleVideoActive = async (video: VideoSourceListItem) => {
    if (!selectedEpisodeId) return;
    try {
      await adminAPI.updateVideoSource(video.id, { is_active: !video.is_active });
      await loadVideoSources(selectedEpisodeId);
    } catch (err: any) {
      alert(err.message || 'Failed to update video source');
    }
  };

  const handleUpdateVideoPriority = async (videoId: string, priority: number) => {
    if (!selectedEpisodeId) return;
    try {
      await adminAPI.updateVideoSource(videoId, { priority });
      await loadVideoSources(selectedEpisodeId);
    } catch (err: any) {
      alert(err.message || 'Failed to update priority');
    }
  };

  const handleToggleEpisode = async (episodeId: string, currentActive: boolean) => {
    try {
      await adminAPI.updateEpisode(episodeId, { is_active: !currentActive });
      const episodesData = await adminAPI.listEpisodes(animeId);
      setEpisodes(episodesData.items);
    } catch (err: any) {
      alert(`Failed to update episode: ${err.message}`);
    }
  };

  return (
    <RequireAuth>
      <AdminNav />
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="text-sm text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
          >
            ← Back to Anime List
          </button>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
          Edit Anime
        </h1>

        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">Loading...</p>
          </div>
        )}

        {error && (
          <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4 mb-6">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {anime && (
          <div className="space-y-8">
            {/* Anime Details Form */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Anime Details
                </h2>
                <form onSubmit={handleSave} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Title
                    </label>
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Description
                    </label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      rows={4}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Status
                    </label>
                    <select
                      value={status}
                      onChange={(e) => setStatus(e.target.value)}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                    >
                      <option value="">Select status</option>
                      <option value="ongoing">Ongoing</option>
                      <option value="completed">Completed</option>
                      <option value="upcoming">Upcoming</option>
                    </select>
                  </div>

                  <div className="flex items-center">
                    <input
                      id="is-active"
                      type="checkbox"
                      checked={isActive}
                      onChange={(e) => setIsActive(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600"
                    />
                    <label htmlFor="is-active" className="ml-2 block text-sm text-gray-900 dark:text-white">
                      Active
                    </label>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={isSaving}
                      className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSaving ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </form>

                <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-sm text-gray-500 dark:text-gray-400 space-y-1">
                    <p><strong>Source:</strong> {anime.source_name} / {anime.source_id}</p>
                    <p><strong>Slug:</strong> {anime.slug}</p>
                    <p><strong>Modified by Admin:</strong> {anime.admin_modified ? 'Yes' : 'No'}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Episodes List */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Episodes ({episodes.length})
                </h2>
                {/* Episode create */}
                <form onSubmit={handleCreateEpisode} className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-5">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Number</label>
                    <input
                      type="number"
                      required
                      value={episodeForm.number}
                      onChange={(e) => setEpisodeForm((f) => ({ ...f, number: e.target.value }))}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Title</label>
                    <input
                      type="text"
                      value={episodeForm.title}
                      onChange={(e) => setEpisodeForm((f) => ({ ...f, title: e.target.value }))}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Source Episode ID</label>
                    <input
                      type="text"
                      required
                      value={episodeForm.source_episode_id}
                      onChange={(e) => setEpisodeForm((f) => ({ ...f, source_episode_id: e.target.value }))}
                      className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div className="flex items-end space-x-2">
                    <label className="inline-flex items-center text-sm text-gray-700 dark:text-gray-300">
                      <input
                        type="checkbox"
                        checked={episodeForm.is_active}
                        onChange={(e) => setEpisodeForm((f) => ({ ...f, is_active: e.target.checked }))}
                        className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600"
                      />
                      Active
                    </label>
                  </div>
                  <div className="flex items-end">
                    <button
                      type="submit"
                      className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
                    >
                      Add Episode
                    </button>
                  </div>
                </form>
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
                  <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                          Episode
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">
                          Title
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">
                          Status
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                       {episodes.length === 0 ? (
                         <tr>
                           <td colSpan={3} className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                             No episodes yet
                           </td>
                         </tr>
                       ) : (
                         episodes.map((ep) => (
                           <tr
                             key={ep.id}
                             className={!ep.is_active ? 'bg-gray-50 dark:bg-gray-900/40' : ''}
                           >
                             <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 dark:text-white">
                               Episode {ep.number}
                             </td>
                             <td className="px-3 py-4 text-sm text-gray-500 dark:text-gray-400 space-y-1">
                               <div>{ep.title || '-'}</div>
                               <div className="flex items-center space-x-2">
                                 <span
                                   className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                                     ep.is_active
                                       ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                                       : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                                   }`}
                                 >
                                   {ep.is_active ? 'Active' : 'Inactive'}
                                 </span>
                                 <span
                                   className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                                     ep.has_video
                                       ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                                       : 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'
                                   }`}
                                 >
                                   {ep.has_video ? 'Has video' : 'No video'}
                                 </span>
                               </div>
                             </td>
                             <td className="px-3 py-4 text-sm space-x-2">
                               <button
                                 onClick={() => handleToggleEpisode(ep.id, ep.is_active)}
                                 className="rounded-md bg-gray-200 dark:bg-gray-700 px-2 py-1 text-xs font-semibold text-gray-800 dark:text-gray-100"
                               >
                                 {ep.is_active ? 'Disable' : 'Enable'}
                               </button>
                               <button
                                 onClick={() => handleSelectEpisode(ep.id)}
                                 className={`rounded-md px-2 py-1 text-xs font-semibold ${
                                   selectedEpisodeId === ep.id
                                     ? 'bg-blue-600 text-white'
                                     : 'bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-300 border border-blue-200 dark:border-blue-700'
                                 }`}
                               >
                                 Video Sources
                               </button>
                             </td>
                           </tr>
                         ))
                       )}
                    </tbody>
                  </table>
                </div>

                {/* Video Sources Section */}
                {selectedEpisodeId && (
                  <div className="mt-6 space-y-4">
                    <h3 className="text-md font-semibold text-gray-900 dark:text-white">
                      Video Sources for Episode {episodes.find((e) => e.id === selectedEpisodeId)?.number}
                    </h3>
                    {isVideoLoading && (
                      <div className="text-sm text-gray-600 dark:text-gray-400">Loading video sources...</div>
                    )}
                    {videoError && (
                      <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-3 text-sm text-red-800 dark:text-red-200">
                        {videoError}
                      </div>
                    )}
                    <form onSubmit={handleCreateVideo} className="grid grid-cols-1 gap-4 md:grid-cols-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Type</label>
                        <input
                          type="text"
                          value={videoCreateForm.type}
                          onChange={(e) => setVideoCreateForm((f) => ({ ...f, type: e.target.value }))}
                          className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">URL</label>
                        <input
                          type="url"
                          required
                          value={videoCreateForm.url}
                          onChange={(e) => setVideoCreateForm((f) => ({ ...f, url: e.target.value }))}
                          className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Source Name</label>
                        <input
                          type="text"
                          required
                          value={videoCreateForm.source_name}
                          onChange={(e) => setVideoCreateForm((f) => ({ ...f, source_name: e.target.value }))}
                          className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Priority</label>
                        <input
                          type="number"
                          value={videoCreateForm.priority}
                          onChange={(e) => setVideoCreateForm((f) => ({ ...f, priority: e.target.value }))}
                          className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-white"
                        />
                      </div>
                      <div className="flex items-end space-x-2">
                        <label className="inline-flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <input
                            type="checkbox"
                            checked={videoCreateForm.is_active}
                            onChange={(e) => setVideoCreateForm((f) => ({ ...f, is_active: e.target.checked }))}
                            className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600"
                          />
                          Active
                        </label>
                      </div>
                      <div className="flex items-end">
                        <button
                          type="submit"
                          className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
                        >
                          Add Video
                        </button>
                      </div>
                    </form>

                    <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
                      <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-900">
                          <tr>
                            <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-white">Type</th>
                            <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">URL</th>
                            <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Priority</th>
                            <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Active</th>
                            <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                          {videoSources.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                                No video sources
                              </td>
                            </tr>
                          ) : (
                            videoSources.map((vs) => (
                            <tr key={vs.id} className={!vs.is_active ? 'bg-gray-50 dark:bg-gray-900/40' : ''}>
                              <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 dark:text-white">
                                {vs.type}
                              </td>
                                <td className="px-3 py-4 text-sm text-blue-600 dark:text-blue-300 break-all">
                                  {vs.url}
                                </td>
                                <td className="px-3 py-4 text-sm text-gray-900 dark:text-white">
                                  <input
                                    type="number"
                                    defaultValue={vs.priority}
                                    onBlur={(e) => {
                                      const value = Number(e.target.value);
                                      if (!Number.isNaN(value) && value !== vs.priority) {
                                        handleUpdateVideoPriority(vs.id, value);
                                      }
                                    }}
                                    className="w-20 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-2 py-1 text-gray-900 dark:text-white"
                                  />
                                </td>
                                <td className="px-3 py-4 text-sm">
                                  <button
                                    onClick={() => handleToggleVideoActive(vs)}
                                    className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                                      vs.is_active
                                        ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                                        : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                                    }`}
                                  >
                                    {vs.is_active ? 'Active' : 'Inactive'}
                                  </button>
                                </td>
                              <td className="px-3 py-4 text-sm space-x-2"></td>
                            </tr>
                          ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </RequireAuth>
  );
}
