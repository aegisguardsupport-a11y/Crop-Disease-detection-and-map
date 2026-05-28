import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { memo } from 'react';

import { PressableScale } from '@/components/ui/pressable-scale';
import { Text, View } from '@/tw';
import { cn } from '@/utils/cn';
import { severityVisuals, timeAgo } from '@/utils/severity';

import type { Report } from '../../types';

interface ReportCardProps {
  report: Report;
  onPress?: (report: Report) => void;
  className?: string;
}

function ReportCardImpl({ report, onPress, className }: ReportCardProps) {
  const visuals = severityVisuals(report.severity);

  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={`${report.crop} report: ${report.disease}`}
      onPress={() => onPress?.(report)}
      pressedScale={0.97}
    >
      <View
        className={cn(
          'h-56 w-44 overflow-hidden rounded-3xl border border-border bg-surface',
          className,
        )}
      >
        <Image
          source={{ uri: report.imageUrl }}
          style={{ width: '100%', height: '100%' }}
          contentFit="cover"
          transition={250}
          cachePolicy="memory-disk"
          recyclingKey={report.id}
          placeholder={{ blurhash: 'L9F$kBM{IUM{ofWBWBay9F%MofRj' }}
        />

        {/* severity dot */}
        <View
          className="absolute right-3 top-3 h-3 w-3 rounded-full border border-white/40"
          style={{ backgroundColor: visuals.rawColor }}
        />

        {/* gradient overlay for legibility */}
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.85)']}
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 0,
            height: '60%',
          }}
        />

        <View className="absolute bottom-0 left-0 right-0 gap-1 p-3">
          <Text className="text-[11px] font-medium uppercase tracking-wider text-white/70">
            {report.crop}
          </Text>
          <Text className="text-base font-semibold text-white" numberOfLines={1}>
            {report.disease}
          </Text>
          <Text className="text-[11px] text-white/60">{timeAgo(report.createdAt)}</Text>
        </View>
      </View>
    </PressableScale>
  );
}

export const ReportCard = memo(ReportCardImpl);
