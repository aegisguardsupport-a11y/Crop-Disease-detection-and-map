import { GlassView } from 'expo-glass-effect';
import { LinearGradient } from 'expo-linear-gradient';
import { memo, useEffect, useState } from 'react';
import { Platform } from 'react-native';

import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';
import { cn } from '@/utils/cn';

interface StatCardProps {
  label: string;
  value: number;
  deltaPercent?: number;
  history?: number[];
  className?: string;
  variant?: 'brand' | 'surface';
}

const COUNT_DURATION_MS = 900;

function useAnimatedCounter(target: number, durationMs = COUNT_DURATION_MS): number {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let frame = 0;
    const start = Date.now();
    const initial = display;
    const tick = () => {
      const elapsed = Date.now() - start;
      const t = Math.min(1, elapsed / durationMs);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(initial + (target - initial) * eased));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, durationMs]);

  return display;
}

function StatCardImpl({
  label,
  value,
  deltaPercent,
  history,
  className,
  variant = 'surface',
}: StatCardProps) {
  const theme = useTheme();
  const display = useAnimatedCounter(value);

  const trendUp = (deltaPercent ?? 0) > 0;
  const trendDown = (deltaPercent ?? 0) < 0;

  const isBrand = variant === 'brand';

  const inner = (
    <View
      className={cn(
        'rounded-3xl border border-border p-4',
        className,
      )}
    >
      {isBrand ? (
        <LinearGradient
          colors={[palette.brand[500], palette.brand[600]]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            borderRadius: 24,
            opacity: 0.95,
          }}
        />
      ) : null}

      <Text
        className={cn(
          'text-[11px] font-medium uppercase tracking-wider',
          isBrand ? 'text-white/80' : 'text-text-muted',
        )}
      >
        {label}
      </Text>

      <View className="mt-1.5 flex-row items-baseline gap-2">
        <Text className={cn('text-3xl font-bold', isBrand ? 'text-white' : 'text-text')}>
          {display}
        </Text>
        {typeof deltaPercent === 'number' ? (
          <Text
            className={cn(
              'text-xs font-semibold',
              isBrand
                ? 'text-white/90'
                : trendUp
                  ? 'text-danger'
                  : trendDown
                    ? 'text-success'
                    : 'text-text-muted',
            )}
          >
            {trendUp ? '▲' : trendDown ? '▼' : '→'} {Math.abs(deltaPercent)}%
          </Text>
        ) : null}
      </View>

      {history && history.length > 0 ? (
        <View className="mt-3 h-8 flex-row items-end gap-1">
          {history.map((h, i) => {
            const max = Math.max(...history, 1);
            const heightPct = Math.max(15, (h / max) * 100);
            return (
              <View
                key={i}
                className="flex-1 rounded-sm"
                style={{
                  height: `${heightPct}%`,
                  backgroundColor: isBrand
                    ? 'rgba(255,255,255,0.55)'
                    : `${theme.primary}80`,
                }}
              />
            );
          })}
        </View>
      ) : null}
    </View>
  );

  if (isBrand) {
    return <View className="overflow-hidden rounded-3xl">{inner}</View>;
  }

  return (
    <GlassView
      glassEffectStyle="regular"
      tintColor={Platform.OS === 'ios' ? `${theme.surfaceElevated}AA` : theme.surfaceElevated}
      style={{ borderRadius: 24, overflow: 'hidden' }}
    >
      {inner}
    </GlassView>
  );
}

export const StatCard = memo(StatCardImpl);
