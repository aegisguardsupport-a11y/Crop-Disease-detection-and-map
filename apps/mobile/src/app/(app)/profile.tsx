import { BottomSheetModal } from '@gorhom/bottom-sheet';
import { Bell, ChevronRight, Globe, MapPin, Plus, Radius, Shield } from 'lucide-react-native';
import { useRef, useState } from 'react';
import { Pressable, ScrollView } from 'react-native';
import Animated, { FadeIn, FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Avatar } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { Chip } from '@/components/ui/chip';
import { SectionLabel } from '@/components/ui/section-label';
import type { Plot } from '@/features/plots/api/plots.api';
import { PlotCard, PlotFormSheet } from '@/features/plots/components';
import { useActivePlots } from '@/features/plots/hooks/use-plots';
import { onboardingStorage } from '@/features/plots/onboarding-storage';
import { MapPickerSheet } from '@/features/upload-report/components/map-picker-sheet';
import { useAuthStore } from '@/store/auth.store';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

export default function ProfileScreen() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { data: plots } = useActivePlots();

  const [editingPlot, setEditingPlot] = useState<Plot | null>(null);
  const formRef = useRef<BottomSheetModal>(null);
  const mapPickerRef = useRef<BottomSheetModal>(null);

  const location = [user?.district, user?.state].filter(Boolean).join(', ') || 'Not set';
  const role = (user?.role ?? 'farmer').toLowerCase();
  const roleLabel = role[0].toUpperCase() + role.slice(1);

  const handleLogout = async () => {
    await onboardingStorage.setSkipped(false);
    await logout();
  };

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top']} style={{ flex: 1 }}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 140, gap: 16 }}
        >
          <Animated.View entering={FadeIn.duration(300)} className="items-center gap-2 pt-4">
            <Avatar name={user?.name} fallback="🌾" size="xl" verified />
            <Text className="text-2xl font-extrabold tracking-tight text-text">
              {user?.name ?? 'Welcome'}
            </Text>
            <Text className="text-sm text-text-muted">+91 {user?.phone ?? '—'}</Text>
            <View className="flex-row gap-2">
              <Chip label={roleLabel} active />
              <Chip label="Verified" tone="success" />
            </View>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(80).duration(400)}>
            <SectionLabel>Your activity</SectionLabel>
            <View className="mt-2">
              <Card padding="none">
                <ListRow
                  isFirst
                  icon={<Shield size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Reports submitted"
                  value="—"
                  onPress={() => undefined}
                />
                <ListRow
                  icon={<MapPin size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Plots"
                  value={String(plots?.length ?? 0)}
                  onPress={() => formRef.current?.present()}
                />
              </Card>
            </View>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(140).duration(400)}>
            <View className="flex-row items-center justify-between px-1">
              <SectionLabel>Plots</SectionLabel>
              <Pressable
                accessibilityRole="button"
                onPress={() => {
                  setEditingPlot(null);
                  formRef.current?.present();
                }}
              >
                <View className="flex-row items-center gap-1">
                  <Plus size={12} color={palette.brand[700]} strokeWidth={2.4} />
                  <Text className="text-xs font-bold text-brand-700">Add plot</Text>
                </View>
              </Pressable>
            </View>
            <View className="mt-2 gap-2">
              {plots && plots.length > 0 ? (
                plots.map((plot) => (
                  <PlotCard
                    key={plot.id}
                    plot={plot}
                    onPress={(p) => {
                      setEditingPlot(p);
                      formRef.current?.present();
                    }}
                  />
                ))
              ) : (
                <View className="items-center gap-2 rounded-xl border border-dashed border-border bg-surface-muted px-4 py-6">
                  <Text className="text-sm font-bold text-text">No plots yet</Text>
                  <Text className="max-w-[260px] text-center text-xs text-text-muted">
                    Add your first field to start receiving outbreak notifications.
                  </Text>
                </View>
              )}
            </View>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(200).duration(400)}>
            <SectionLabel>Settings</SectionLabel>
            <View className="mt-2">
              <Card padding="none">
                <ListRow
                  isFirst
                  icon={<Bell size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Notifications"
                  value="On"
                  onPress={() => undefined}
                />
                <ListRow
                  icon={<Radius size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Alert radius"
                  value="5 km"
                  onPress={() => undefined}
                />
                <ListRow
                  icon={<Globe size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Language"
                  value="English"
                  onPress={() => undefined}
                />
                <ListRow
                  icon={<MapPin size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Location"
                  value={location}
                  onPress={() => undefined}
                />
              </Card>
            </View>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(260).duration(400)}>
            <Pressable
              accessibilityRole="button"
              onPress={handleLogout}
              className="flex-row items-center justify-center rounded-xl border border-danger-tint bg-surface px-4 py-3"
            >
              <Text className="text-sm font-bold text-danger">Sign out</Text>
            </Pressable>
          </Animated.View>
        </ScrollView>
      </SafeAreaView>

      <PlotFormSheet
        ref={formRef}
        plot={editingPlot}
        onOpenMapPicker={() => mapPickerRef.current?.present()}
      />
      <MapPickerSheet
        ref={mapPickerRef}
        initialLocation={null}
        onConfirm={() => formRef.current?.present()}
      />
    </View>
  );
}

interface ListRowProps {
  icon: React.ReactNode;
  label: string;
  value?: string;
  onPress?: () => void;
  destructive?: boolean;
  isFirst?: boolean;
}

function ListRow({ icon, label, value, onPress, destructive, isFirst }: ListRowProps) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress}>
      <View
        className={`flex-row items-center gap-3 px-4 py-3 ${
          isFirst ? '' : 'border-t border-border'
        }`}
      >
        <View className="h-9 w-9 items-center justify-center rounded-xl bg-brand-50">{icon}</View>
        <View className="flex-1">
          <Text
            className={destructive ? 'text-sm font-bold text-danger' : 'text-sm font-bold text-text'}
          >
            {label}
          </Text>
          {value ? <Text className="text-xs text-text-muted">{value}</Text> : null}
        </View>
        {onPress ? <ChevronRight size={16} color={palette.brand[700]} strokeWidth={2.2} /> : null}
      </View>
    </Pressable>
  );
}
