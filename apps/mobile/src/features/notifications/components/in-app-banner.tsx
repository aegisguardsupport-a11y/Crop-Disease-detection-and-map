import { GlassView } from 'expo-glass-effect';
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { AlertTriangle, Bell, Camera, Info, X } from 'lucide-react-native';
import { useEffect, useState } from 'react';
import { Platform, Pressable } from 'react-native';
import Animated, { FadeInUp, FadeOutUp } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useTheme } from '@/hooks/use-theme';
import { Text, View } from '@/tw';
import { severityVisuals } from '@/utils/severity';

import type { Notification } from '../api/notifications.api';

interface InAppBannerProps {
  notification: Notification;
  onDismiss: (id: string) => void;
}

const ICON_FOR_TYPE = {
  OUTBREAK: AlertTriangle,
  REPORT: Camera,
  WARNING: AlertTriangle,
  SYSTEM: Info,
} as const;

const AUTO_DISMISS_MS = 4500;

export function InAppBanner({ notification: n, onDismiss }: InAppBannerProps) {
  const theme = useTheme();
  const visuals = severityVisuals(n.severity);
  const Icon = ICON_FOR_TYPE[n.type] ?? Bell;

  useEffect(() => {
    const id = setTimeout(() => onDismiss(n.id), AUTO_DISMISS_MS);
    return () => clearTimeout(id);
  }, [n.id, onDismiss]);

  const handlePress = () => {
    Haptics.selectionAsync().catch(() => undefined);
    onDismiss(n.id);
    // Navigate based on notification data
    const data = n.data as Record<string, unknown> | null;
    const outbreakId = data?.outbreakId as string | undefined;
    const reportId = data?.reportId as string | undefined;
    if (outbreakId) {
      router.push('/map');
    } else if (reportId) {
      router.push({ pathname: '/reports/[id]', params: { id: reportId } });
    } else {
      router.push('/notifications');
    }
  };

  return (
    <Animated.View entering={FadeInUp.duration(280)} exiting={FadeOutUp.duration(220)}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={n.title}
        onPress={handlePress}
        style={({ pressed }) => ({ opacity: pressed ? 0.92 : 1 })}
      >
        <GlassView
          glassEffectStyle="regular"
          tintColor={
            Platform.OS === 'ios' ? `${theme.surfaceElevated}DD` : `${theme.surfaceElevated}EE`
          }
          style={{ borderRadius: 20, overflow: 'hidden', marginHorizontal: 12 }}
        >
          <View
            className="flex-row items-start gap-3 rounded-[20px] border border-border p-3"
            style={{
              shadowColor: '#000',
              shadowOpacity: 0.18,
              shadowRadius: 12,
              shadowOffset: { width: 0, height: 4 },
              elevation: 6,
            }}
          >
            <View
              className="mt-0.5 h-10 w-10 items-center justify-center rounded-2xl"
              style={{ backgroundColor: `${visuals.rawColor}22` }}
            >
              <Icon size={18} color={visuals.rawColor} strokeWidth={2.2} />
            </View>
            <View className="flex-1 gap-0.5">
              <Text className="text-sm font-semibold text-text" numberOfLines={1}>
                {n.title}
              </Text>
              <Text className="text-xs text-text-muted" numberOfLines={2}>
                {n.body}
              </Text>
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Dismiss"
              onPress={() => onDismiss(n.id)}
              hitSlop={8}
              className="h-7 w-7 items-center justify-center rounded-full bg-surface"
            >
              <X size={14} color={theme.textMuted} strokeWidth={2} />
            </Pressable>
          </View>
        </GlassView>
      </Pressable>
    </Animated.View>
  );
}

interface InAppBannerStackProps {
  banners: Notification[];
  onDismiss: (id: string) => void;
}

const MAX_VISIBLE = 3;

export function InAppBannerStack({ banners, onDismiss }: InAppBannerStackProps) {
  const visible = banners.slice(-MAX_VISIBLE);
  if (visible.length === 0) return null;

  return (
    <SafeAreaView
      edges={['top']}
      pointerEvents="box-none"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
      }}
    >
      <View pointerEvents="box-none" style={{ gap: 8, paddingTop: 4 }}>
        {visible.map((b) => (
          <InAppBanner key={b.id} notification={b} onDismiss={onDismiss} />
        ))}
      </View>
    </SafeAreaView>
  );
}

// state-driven helper used by the provider
export function useBannerStack(): {
  banners: Notification[];
  push: (n: Notification) => void;
  dismiss: (id: string) => void;
} {
  const [banners, setBanners] = useState<Notification[]>([]);
  const push = (n: Notification) => {
    setBanners((prev) => [...prev.filter((b) => b.id !== n.id), n]);
  };
  const dismiss = (id: string) => {
    setBanners((prev) => prev.filter((b) => b.id !== id));
  };
  return { banners, push, dismiss };
}
