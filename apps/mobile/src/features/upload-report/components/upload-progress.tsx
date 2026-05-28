import { GlassView } from 'expo-glass-effect';
import { LinearGradient } from 'expo-linear-gradient';
import { ActivityIndicator, Platform } from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';

import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

import type { UploadState } from '../types';
import { STATE_LABELS } from '../utils/upload-states';

interface UploadProgressProps {
  state: UploadState;
  progress: number; // 0-100
  errorMessage?: string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
}

const ACTIVE_STATES: UploadState[] = ['compressing', 'uploading', 'processing'];

export function UploadProgress({
  state,
  progress,
  errorMessage,
  onRetry: _onRetry,
  onDismiss: _onDismiss,
}: UploadProgressProps) {
  const theme = useTheme();
  if (state === 'idle' || state === 'success') return null;

  const isActive = ACTIVE_STATES.includes(state);
  const showBar = state === 'uploading';
  const isQueued = state === 'queued-offline';
  const isFailed = state === 'failed';

  return (
    <Animated.View entering={FadeIn.duration(200)}>
      <GlassView
        glassEffectStyle="regular"
        tintColor={Platform.OS === 'ios' ? `${theme.surfaceElevated}AA` : theme.surfaceElevated}
        style={{ borderRadius: 20, overflow: 'hidden' }}
      >
        <View
          className={`gap-2 rounded-[20px] border p-3 ${
            isFailed
              ? 'border-danger/40'
              : isQueued
                ? 'border-warning/40'
                : 'border-border'
          }`}
        >
          <View className="flex-row items-center gap-3">
            {isActive ? (
              <ActivityIndicator color={palette.brand[400]} />
            ) : (
              <View
                className={`h-2.5 w-2.5 rounded-full ${
                  isFailed ? 'bg-danger' : isQueued ? 'bg-warning' : 'bg-brand-500'
                }`}
              />
            )}
            <Text className="flex-1 text-sm font-semibold text-text">
              {STATE_LABELS[state]}
            </Text>
            {showBar ? (
              <Text className="text-xs font-semibold text-text-muted">{progress}%</Text>
            ) : null}
          </View>

          {showBar ? (
            <View className="h-1.5 w-full overflow-hidden rounded-full bg-surface">
              <View
                className="h-full rounded-full"
                style={{ width: `${Math.max(4, progress)}%`, backgroundColor: palette.brand[500] }}
              />
            </View>
          ) : null}

          {isQueued ? (
            <Text className="text-xs text-text-muted">
              You&apos;re offline. We&apos;ll upload this report automatically when you&apos;re back online.
            </Text>
          ) : null}

          {isFailed && errorMessage ? (
            <Text className="text-xs text-danger">{errorMessage}</Text>
          ) : null}
        </View>
      </GlassView>
    </Animated.View>
  );
}

export function GradientSubmitButton({
  label,
  loading,
  disabled,
  onPress,
}: {
  label: string;
  loading?: boolean;
  disabled?: boolean;
  onPress: () => void;
}) {
  return (
    <View className="overflow-hidden rounded-2xl">
      <LinearGradient
        colors={[palette.brand[500], palette.brand[600]]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View
          accessibilityRole="button"
          style={{ opacity: disabled ? 0.5 : 1 }}
          className="h-14 flex-row items-center justify-center gap-2 px-5"
          onTouchEnd={() => {
            if (!disabled && !loading) onPress();
          }}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text className="text-base font-semibold text-white">{label}</Text>
          )}
        </View>
      </LinearGradient>
    </View>
  );
}
