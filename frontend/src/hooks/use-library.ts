"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { backendAPI, type LibraryItem, type LibraryStatus } from "@/lib/api/backend";

/**
 * Hook for user library management.
 * Falls back to local storage when user is not authenticated.
 */
export function useLibrary(params?: {
  provider?: string;
  status?: LibraryStatus;
  favorites?: boolean;
}) {
  const queryClient = useQueryClient();
  const isAuthenticated = backendAPI.isAuthenticated();

  // Query for library items
  const { data: items = [], isLoading, error } = useQuery({
    queryKey: ['library', params],
    queryFn: () => backendAPI.getLibrary(params),
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
  });

  // Mutation to add/update library item
  const updateMutation = useMutation({
    mutationFn: ({
      titleId,
      status,
      isFavorite,
      provider = 'rpc',
    }: {
      titleId: string;
      status?: LibraryStatus;
      isFavorite?: boolean;
      provider?: string;
    }) =>
      backendAPI.updateLibraryItem(
        titleId,
        { status, is_favorite: isFavorite },
        provider
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
  });

  // Mutation to delete library item
  const deleteMutation = useMutation({
    mutationFn: ({ titleId, provider = 'rpc' }: { titleId: string; provider?: string }) =>
      backendAPI.deleteLibraryItem(titleId, provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
  });

  return {
    items,
    isLoading,
    error,
    isAuthenticated,
    updateItem: updateMutation.mutate,
    deleteItem: deleteMutation.mutate,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}

/**
 * Hook to check if a title is in the library.
 */
export function useIsInLibrary(titleId: string, provider: string = 'rpc') {
  const { items } = useLibrary({ provider });
  
  const item = items.find(
    (i) => i.title_id === titleId && i.provider === provider
  );
  
  return {
    isInLibrary: !!item,
    item,
    status: item?.status,
    isFavorite: item?.is_favorite || false,
  };
}
