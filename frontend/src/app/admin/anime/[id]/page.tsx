'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { RequireAuth } from '@/components/admin/require-auth';
import { AdminNav } from '@/components/admin/admin-nav';
import { adminAPI, type AnimeDetail, type EpisodeListItem } from '@/lib/admin-api';

export default function AnimeEditPage() {
  const params = useParams();
  const router = useRouter();
  const animeId = params.id as string;

  const [anime, setAnime] = useState<AnimeDetail | null>(null);
  const [episodes, setEpisodes] = useState<EpisodeListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [year, setYear] = useState<number | ''>('');
  const [status, setStatus] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

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
        setYear(animeData.year || '');
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
        year: year || undefined,
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

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Year
                      </label>
                      <input
                        type="number"
                        value={year}
                        onChange={(e) => setYear(e.target.value ? parseInt(e.target.value) : '')}
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
                          <tr key={ep.id}>
                            <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 dark:text-white">
                              Episode {ep.number}
                            </td>
                            <td className="px-3 py-4 text-sm text-gray-500 dark:text-gray-400">
                              {ep.title || '-'}
                            </td>
                            <td className="px-3 py-4 text-sm">
                              <button
                                onClick={() => handleToggleEpisode(ep.id, ep.is_active)}
                                className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                                  ep.is_active
                                    ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                                    : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                                }`}
                              >
                                {ep.is_active ? 'Active' : 'Inactive'}
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </RequireAuth>
  );
}
