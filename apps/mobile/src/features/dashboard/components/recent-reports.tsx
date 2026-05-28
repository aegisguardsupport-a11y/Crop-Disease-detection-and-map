import { router } from 'expo-router';
import { ChevronRight } from 'lucide-react-native';
import { Pressable } from 'react-native';

import { Card } from '@/components/ui/card';
import { Chip } from '@/components/ui/chip';
import { Skeleton } from '@/components/ui/skeleton';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';
import { timeAgo } from '@/utils/severity';

import type { Report, Severity } from '../types';

interface RecentReportsProps {
  reports?: Report[];
  loading?: boolean;
}

const SEVERITY_TONE: Record<Severity, 'success' | 'warning' | 'danger'> = {
  low: 'success',
  medium: 'warning',
  high: 'danger',
};

const SEVERITY_LABEL: Record<Severity, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
};

export function RecentReports({ reports, loading }: RecentReportsProps) {
  if (loading || !reports) {
    return (
      <View className="gap-2">
        <View className="flex-row items-center justify-between px-1">
          <Text className="text-base font-bold text-text">Latest in your area</Text>
        </View>
        <Skeleton height={180} rounded="xl" />
      </View>
    );
  }

  const top = reports.slice(0, 3);

  return (
    <View className="gap-2">
      <View className="flex-row items-center justify-between px-1">
        <Text className="text-base font-bold tracking-tight text-text">
          Latest in your area
        </Text>
        <Pressable accessibilityRole="button" onPress={() => router.push('/notifications')}>
          <Text className="text-xs font-bold text-brand-700">View all</Text>
        </Pressable>
      </View>

      <Card padding="none">
        {top.length === 0 ? (
          <View className="px-4 py-6">
            <Text className="text-sm text-text-muted">No nearby reports yet.</Text>
          </View>
        ) : (
          top.map((r, i) => (
            <Pressable
              key={r.id}
              accessibilityRole="button"
              onPress={() => router.push({ pathname: '/reports/[id]', params: { id: r.id } })}
            >
              <View
                className={`flex-row items-center gap-3 px-4 py-3 ${
                  i > 0 ? 'border-t border-border' : ''
                }`}
              >
                <View className="h-10 w-10 items-center justify-center rounded-xl bg-brand-50">
                  <Text className="text-lg">🌿</Text>
                </View>
                <View className="flex-1 gap-0.5">
                  <Text className="text-sm font-bold text-text" numberOfLines={1}>
                    {r.crop} · {r.disease}
                  </Text>
                  <Text className="text-xs text-text-subtle">{timeAgo(r.createdAt)}</Text>
                </View>
                {r.severity ? (
                  <Chip
                    label={SEVERITY_LABEL[r.severity]}
                    tone={SEVERITY_TONE[r.severity] ?? 'warning'}
                  />
                ) : null}
                <ChevronRight size={16} color={palette.brand[700]} strokeWidth={2.2} />
              </View>
            </Pressable>
          ))
        )}
      </Card>
    </View>
  );
}
