'use client';

import useSWR from 'swr';
import { getUser } from '@/actions/auth';
import type { User } from '@/lib/types';

export function useUser() {
    const { data, error, isLoading, mutate } = useSWR<User | null>(
        'user',
        async () => {
            const result = await getUser();
            if (result.error) {
                console.error('Error fetching user:', result.error);
                return null;
            }
            return result.data || null;
        },
        {
            revalidateOnFocus: false,
            revalidateOnReconnect: false,
            dedupingInterval: 5000,
        }
    );

    return {
        user: data ?? null,
        isLoading,
        error,
        mutate,
    };
}
