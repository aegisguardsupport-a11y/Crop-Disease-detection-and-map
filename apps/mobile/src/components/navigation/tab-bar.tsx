import type { BottomTabBarProps } from 'expo-router/build/react-navigation/bottom-tabs';
import * as Haptics from 'expo-haptics';
import { LinearGradient } from 'expo-linear-gradient';
import { useEffect } from 'react';
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { PressableScale } from '@/components/ui/pressable-scale';
import { NotificationBadge } from '@/features/notifications/components/notification-badge';
import { useUnreadCount } from '@/features/notifications/hooks/use-notifications';
import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

import { TabBarIcon, type TabIconName } from './tab-bar-icon';

const ROUTE_TO_ICON: Record<string, TabIconName> = {
  index: 'house',
  map: 'map',
  upload: 'plus',
  notifications: 'bell',
  profile: 'user',
};

const ROUTE_TO_LABEL: Record<string, string> = {
  index: 'Home',
  map: 'Map',
  upload: 'Report',
  notifications: 'Alerts',
  profile: 'Profile',
};

export function TabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const unreadCount = useUnreadCount();

  return (
    <View
      pointerEvents="box-none"
      style={{
        position: 'absolute',
        left: 16,
        right: 16,
        bottom: insets.bottom > 0 ? insets.bottom : 12,
      }}
    >
      <View
        className="flex-row items-center justify-between rounded-[22px] border border-border bg-surface px-2 py-2"
        style={{
          shadowColor: '#0f172a',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.06,
          shadowRadius: 16,
          elevation: 8,
        }}
      >
        {state.routes.map((route, index) => {
          const { options } = descriptors[route.key];
          const isFocused = state.index === index;
          const iconName = ROUTE_TO_ICON[route.name] ?? 'house';
          const label = ROUTE_TO_LABEL[route.name] ?? route.name;
          const isFab = iconName === 'plus';

          const onPress = () => {
            const event = navigation.emit({
              type: 'tabPress',
              target: route.key,
              canPreventDefault: true,
            });
            if (!isFocused && !event.defaultPrevented) {
              navigation.navigate(route.name, route.params);
            }
          };

          const onLongPress = () => {
            navigation.emit({ type: 'tabLongPress', target: route.key });
          };

          if (isFab) {
            return (
              <FabTab
                key={route.key}
                label={options.tabBarAccessibilityLabel ?? label}
                onPress={onPress}
                onLongPress={onLongPress}
              />
            );
          }

          const tint = isFocused ? theme.primary : theme.textSubtle;

          return (
            <RegularTab
              key={route.key}
              accessibilityLabel={options.tabBarAccessibilityLabel ?? label}
              isFocused={isFocused}
              iconName={iconName}
              label={label}
              tint={tint}
              onPress={onPress}
              onLongPress={onLongPress}
              badge={
                iconName === 'bell' && unreadCount > 0 ? (
                  <NotificationBadge count={unreadCount} size="sm" />
                ) : null
              }
            />
          );
        })}
      </View>
    </View>
  );
}

interface RegularTabProps {
  accessibilityLabel: string;
  isFocused: boolean;
  iconName: TabIconName;
  label: string;
  tint: string;
  onPress: () => void;
  onLongPress: () => void;
  badge: React.ReactNode;
}

function RegularTab({
  accessibilityLabel,
  isFocused,
  iconName,
  label,
  tint,
  onPress,
  onLongPress,
  badge,
}: RegularTabProps) {
  const focused = useSharedValue(isFocused ? 1 : 0);

  useEffect(() => {
    focused.value = withTiming(isFocused ? 1 : 0, { duration: 180 });
  }, [focused, isFocused]);

  const iconBgStyle = useAnimatedStyle(() => ({
    opacity: focused.value,
  }));

  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityState={isFocused ? { selected: true } : {}}
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      onLongPress={onLongPress}
      pressedScale={0.92}
      haptic="selection"
      className="flex-1 items-center justify-center gap-1 rounded-2xl px-2 py-2"
    >
      <View className="overflow-hidden rounded-lg" style={{ width: 28, height: 28, alignItems: 'center', justifyContent: 'center' }}>
        <Animated.View
          pointerEvents="none"
          style={[
            { position: 'absolute', inset: 0, borderRadius: 8, overflow: 'hidden' },
            iconBgStyle,
          ]}
        >
          <LinearGradient
            colors={[`${palette.brand[500]}26`, `${palette.brand[600]}26`]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={{ position: 'absolute', inset: 0 }}
          />
        </Animated.View>
        <View>
          <TabBarIcon name={iconName} focused={isFocused} color={tint} size={20} />
          {badge ? (
            <View style={{ position: 'absolute', top: -4, right: -8 }}>{badge}</View>
          ) : null}
        </View>
      </View>
      <Text
        className="text-[10px] font-bold"
        style={{ color: tint, letterSpacing: 0.3 }}
        numberOfLines={1}
      >
        {label}
      </Text>
    </PressableScale>
  );
}

interface FabTabProps {
  label: string;
  onPress: () => void;
  onLongPress: () => void;
}

/**
 * The center "Report" raised FAB. Sits ~16px above the bar with a brand-tinted
 * shadow, gradient background, and a 3px white ring so it visually separates
 * from the bar.
 */
function FabTab({ label, onPress, onLongPress }: FabTabProps) {
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={() => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => undefined);
        onPress();
      }}
      onLongPress={onLongPress}
      haptic="none"
      pressedScale={0.92}
      className="items-center"
      style={{ transform: [{ translateY: -16 }], width: 56 }}
    >
      <View
        className="h-14 w-14 items-center justify-center overflow-hidden rounded-2xl border-[3px] border-surface"
        style={{
          shadowColor: palette.brand[600],
          shadowOffset: { width: 0, height: 8 },
          shadowOpacity: 0.45,
          shadowRadius: 14,
          elevation: 12,
        }}
      >
        <LinearGradient
          colors={[palette.brand[500], palette.brand[600]]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={{ position: 'absolute', inset: 0 }}
        />
        <TabBarIcon name="plus" focused color="#ffffff" size={26} />
      </View>
    </PressableScale>
  );
}
