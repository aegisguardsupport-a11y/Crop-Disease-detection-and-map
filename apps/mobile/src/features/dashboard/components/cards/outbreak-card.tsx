import { GlassView } from 'expo-glass-effect';
import { memo } from 'react';
import { Platform } from 'react-native';

import { useTheme } from '@/hooks/use-theme';
import { Text, View } from '@/tw';
import { cn } from '@/utils/cn';
import { severityVisuals } from '@/utils/severity';

import type { Outbreak } from '../../types';

interface OutbreakCardProps {
  outbreak: Outbreak;
  className?: string;
}

function OutbreakCardImpl({ outbreak, className }: OutbreakCardProps) {
  const theme = useTheme();
  const visuals = severityVisuals(outbreak.severity);
  const trendUp = outbreak.trendPercent >= 0;

  return (
    <GlassView
      glassEffectStyle="regular"
      tintColor={Platform.OS === 'ios' ? `${theme.surfaceElevated}AA` : theme.surfaceElevated}
      style={{ borderRadius: 24, overflow: 'hidden' }}
    >
      <View
        className={cn(
          'rounded-3xl border border-border p-4',
          className,
        )}
      >
        <View className="flex-row items-start justify-between">
          <View className="flex-1 gap-1 pr-3">
            <Text className="text-base font-semibold text-text" numberOfLines={1}>
              {outbreak.disease}
            </Text>
            <Text className="text-xs text-text-muted">
              {outbreak.cropType} · {outbreak.district}
            </Text>
          </View>
          <View
            className={cn(
              'flex-row items-center gap-1 rounded-full px-2 py-1',
              visuals.bgClass,
            )}
          >
            <View className={cn('h-1.5 w-1.5 rounded-full')} style={{ backgroundColor: visuals.rawColor }} />
            <Text className={cn('text-[10px] font-semibold uppercase tracking-wide', visuals.textClass)}>
              {visuals.label}
            </Text>
          </View>
        </View>

        <View className="mt-3 flex-row items-end justify-between">
          <View>
            <Text className="text-2xl font-bold text-text">{outbreak.affectedVillages}</Text>
            <Text className="text-[11px] text-text-subtle">villages affected</Text>
          </View>
          <View className="items-end">
            <Text
              className={cn(
                'text-sm font-semibold',
                trendUp ? 'text-danger' : 'text-success',
              )}
            >
              {trendUp ? '▲' : '▼'} {Math.abs(outbreak.trendPercent)}%
            </Text>
            <Text className="text-[11px] text-text-subtle">vs last week</Text>
          </View>
        </View>
      </View>
    </GlassView>
  );
}

export const OutbreakCard = memo(OutbreakCardImpl);
