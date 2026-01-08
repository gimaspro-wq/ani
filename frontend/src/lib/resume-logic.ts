/**
 * Resume/Next Episode Logic
 * 
 * Determines whether to resume the current episode or suggest the next one
 * based on watch progress.
 */

export interface WatchProgress {
  animeId: string;
  episodeNumber: number;
  currentTime: number;
  duration: number;
  updatedAt: number;
}

export interface ResumeAction {
  type: 'resume' | 'next';
  episodeNumber: number;
  label: string;
}

/**
 * Completion threshold (90% = user is close enough to the end)
 */
const COMPLETION_THRESHOLD = 0.90;

/**
 * Determine the best action for a user who has watch progress on an anime.
 * 
 * @param progress - The last watched episode's progress
 * @param totalEpisodes - Total number of episodes available (optional)
 * @returns The recommended action (resume or next episode)
 */
export function determineResumeAction(
  progress: WatchProgress,
  totalEpisodes?: number
): ResumeAction {
  const percentComplete = progress.currentTime / progress.duration;
  
  // If user has completed >= 90% of the episode, suggest next episode
  if (percentComplete >= COMPLETION_THRESHOLD) {
    const nextEpisode = progress.episodeNumber + 1;
    
    // Check if there's a next episode available
    if (totalEpisodes && nextEpisode > totalEpisodes) {
      // No next episode available, suggest rewatching
      return {
        type: 'resume',
        episodeNumber: progress.episodeNumber,
        label: 'Rewatch',
      };
    }
    
    return {
      type: 'next',
      episodeNumber: nextEpisode,
      label: `Play Episode ${nextEpisode}`,
    };
  }
  
  // Otherwise, resume the same episode
  return {
    type: 'resume',
    episodeNumber: progress.episodeNumber,
    label: `Resume Episode ${progress.episodeNumber}`,
  };
}

/**
 * Get a formatted progress display string
 */
export function formatProgress(currentTime: number, duration: number): string {
  const percent = Math.round((currentTime / duration) * 100);
  return `${percent}% watched`;
}

/**
 * Format timestamp to relative time (e.g., "2 hours ago", "3 days ago")
 */
export function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;
  
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) {
    return days === 1 ? '1 day ago' : `${days} days ago`;
  }
  if (hours > 0) {
    return hours === 1 ? '1 hour ago' : `${hours} hours ago`;
  }
  if (minutes > 0) {
    return minutes === 1 ? '1 minute ago' : `${minutes} minutes ago`;
  }
  return 'Just now';
}
