import { GlassView } from 'expo-glass-effect';
import { memo } from 'react';
import { Platform } from 'react-native';

import { PressableScale } from '@/components/ui/pressable-scale';
import { useTheme } from '@/hooks/use-theme';
import { Text, View } from '@/tw';
import { cn } from '@/utils/cn';
import { severityVisuals, timeAgo } from '@/utils/severity';

import type { Alert } from '../../types';

interface NotificationPreviewCardProps {
  alert: Alert;
  onPress?: (alert: Alert) => void;
  className?: string;
}

function NotificationPreviewCardImpl({ alert, onPress, className }: NotificationPreviewCardProps) {
  const theme = useTheme();
  const visuals = severityVisuals(alert.severity);

  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={alert.title}
      onPress={() => onPress?.(alert)}
      pressedScale={0.98}
    >
      <GlassView
        glassEffectStyle="regular"
        tintColor={Platform.OS === 'ios' ? `${theme.surfaceElevated}AA` : theme.surfaceElevated}
        style={{ borderRadius: 20, overflow: 'hidden' }}
      >
        <View className={cn('flex-row items-start gap-3 rounded-[20px] border border-border p-3', className)}>
          <View
            className={cn(
              'mt-0.5 h-10 w-10 items-center justify-center rounded-2xl',
              visuals.bgClass,
            )}
          >
            <View className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: visuals.rawColor }} />
          </View>

          <View className="flex-1 gap-0.5">
            <View className="flex-row items-center justify-between gap-2">
              <Text className="flex-1 text-sm font-semibold text-text" numberOfLines={1}>
                {alert.title}
              </Text>
              {alert.unread ? (
                <View className="h-2 w-2 rounded-full bg-brand-500" />
              ) : null}
            </View>
            <Text className="text-xs text-text-muted" numberOfLines={2}>
              {alert.description}
            </Text>
            <Text className="mt-1 text-[11px] text-text-subtle">{timeAgo(alert.createdAt)}</Text>
          </View>
        </View>
      </GlassView>
    </PressableScale>
  );
}

export const NotificationPreviewCard = memo(NotificationPreviewCardImpl);
