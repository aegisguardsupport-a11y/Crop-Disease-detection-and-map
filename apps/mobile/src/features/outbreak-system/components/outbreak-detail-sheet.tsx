import {
  BottomSheetBackdrop,
  BottomSheetModal,
  BottomSheetScrollView,
} from '@gorhom/bottom-sheet';
import { GlassView } from 'expo-glass-effect';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import {
  Activity,
  ChevronRight,
  Clock,
  MapPin,
  Sparkles,
  TrendingUp,
  X,
} from 'lucide-react-native';
import { forwardRef } from 'react';
import { ActivityIndicator, Platform, Pressable } from 'react-native';
import MapView, { Circle, Marker, PROVIDER_GOOGLE } from 'react-native-maps';

import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';
import type { OutbreakZone } from '@/features/map-system/types';
import { CROP_BY_NAME } from '@/constants/crops';
import { timeAgo } from '@/utils/severity';

import { useOutbreak } from '../hooks/use-outbreaks';

import { SeverityIndicator } from './severity-indicator';

interface OutbreakDetailSheetProps {
  outbreak: OutbreakZone | null;
}

export const OutbreakDetailSheet = forwardRef<BottomSheetModal, OutbreakDetailSheetProps>(
  function OutbreakDetailSheet({ outbreak }, ref) {
    const theme = useTheme();
    const { data, isPending } = useOutbreak(outbreak?.id ?? null);

    const dismiss = () => {
      // @ts-expect-error: ref provided
      ref?.current?.dismiss();
    };

    const cropList = outbreak?.affectedCropTypes ?? [];

    return (
      <BottomSheetModal
        ref={ref}
        snapPoints={['45%', '92%']}
        backgroundStyle={{ backgroundColor: theme.surfaceElevated }}
        handleIndicatorStyle={{ backgroundColor: theme.borderStrong }}
        backdropComponent={(props) => (
          <BottomSheetBackdrop
            {...props}
            disappearsOnIndex={-1}
            appearsOnIndex={0}
            opacity={0.45}
          />
        )}
      >
        {!outbreak ? null : (
          <BottomSheetScrollView
            contentContainerStyle={{ padding: 20, paddingBottom: 60, gap: 16 }}
          >
            <View className="flex-row items-start justify-between">
              <View className="flex-1 gap-1">
                <View className="flex-row items-center gap-2">
                  <Text className="text-[11px] font-medium uppercase tracking-wider text-text-subtle">
                    Outbreak
                  </Text>
                  {!outbreak.active ? (
                    <View className="rounded-full bg-text-subtle/15 px-2 py-0.5">
                      <Text className="text-[10px] font-semibold uppercase tracking-wider text-text-subtle">
                        Resolved
                      </Text>
                    </View>
                  ) : null}
                </View>
                <Text className="text-2xl font-bold text-text" numberOfLines={2}>
                  {outbreak.disease}
                </Text>
                <View className="mt-1 flex-row items-center gap-2">
                  <SeverityIndicator severity={outbreak.severity} variant="expanded" />
                </View>
              </View>
              <Pressable
                accessibilityRole="button"
                onPress={dismiss}
                className="h-9 w-9 items-center justify-center rounded-full bg-surface"
              >
                <X size={18} color={theme.text} strokeWidth={2} />
              </Pressable>
            </View>

            {/* Stats grid */}
            <GlassView
              glassEffectStyle="regular"
              tintColor={
                Platform.OS === 'ios' ? `${theme.surfaceElevated}AA` : theme.surfaceElevated
              }
              style={{ borderRadius: 24, overflow: 'hidden' }}
            >
              <View className="flex-row flex-wrap rounded-3xl border border-border">
                <Stat
                  icon={<Activity size={14} color={theme.textMuted} strokeWidth={2.2} />}
                  label="Reports"
                  value={`${outbreak.reportCount}`}
                />
                <Stat
                  icon={<TrendingUp size={14} color={theme.textMuted} strokeWidth={2.2} />}
                  label="High severity"
                  value={`${outbreak.highCount}`}
                />
                <Stat
                  icon={<MapPin size={14} color={theme.textMuted} strokeWidth={2.2} />}
                  label="Radius"
                  value={`${(outbreak.radius / 1000).toFixed(1)} km`}
                />
                <Stat
                  icon={<Clock size={14} color={theme.textMuted} strokeWidth={2.2} />}
                  label="Last report"
                  value={timeAgo(outbreak.lastSeenAt)}
                />
              </View>
            </GlassView>

            {/* Affected crops */}
            {cropList.length > 0 ? (
              <View className="gap-2">
                <Text className="text-[11px] font-medium uppercase tracking-wider text-text-subtle">
                  Affected crops
                </Text>
                <View className="flex-row flex-wrap gap-2">
                  {cropList.map((crop) => {
                    const known = CROP_BY_NAME[crop.toLowerCase()];
                    return (
                      <View
                        key={crop}
                        className="flex-row items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1.5"
                      >
                        {known ? <Text className="text-base">{known.emoji}</Text> : null}
                        <Text className="text-xs font-semibold text-text">{crop}</Text>
                      </View>
                    );
                  })}
                </View>
              </View>
            ) : null}

            {/* Mini map preview */}
            <View
              className="h-44 overflow-hidden rounded-3xl border border-border"
              style={{ backgroundColor: theme.surface }}
            >
              <MapView
                style={{ flex: 1 }}
                provider={Platform.OS === 'android' ? PROVIDER_GOOGLE : undefined}
                pointerEvents="none"
                initialRegion={{
                  latitude: outbreak.latitude,
                  longitude: outbreak.longitude,
                  latitudeDelta: ((outbreak.radius / 1000) * 3) / 110,
                  longitudeDelta: ((outbreak.radius / 1000) * 3) / 110,
                }}
                liteMode
                scrollEnabled={false}
                zoomEnabled={false}
                rotateEnabled={false}
                pitchEnabled={false}
              >
                <Circle
                  center={{ latitude: outbreak.latitude, longitude: outbreak.longitude }}
                  radius={outbreak.radius}
                  fillColor="rgba(239, 68, 68, 0.18)"
                  strokeColor="rgba(239, 68, 68, 0.65)"
                  strokeWidth={2}
                />
                <Marker
                  coordinate={{ latitude: outbreak.latitude, longitude: outbreak.longitude }}
                  pinColor={palette.brand[600]}
                  tracksViewChanges={false}
                />
              </MapView>
            </View>

            {/* Contributing reports */}
            <View className="gap-2">
              <Text className="text-base font-semibold text-text">Recent contributing reports</Text>
              {isPending ? (
                <View className="items-center py-6">
                  <ActivityIndicator color={palette.brand[400]} />
                </View>
              ) : !data?.contributingReports.length ? (
                <Text className="text-xs text-text-muted">No contributing reports yet.</Text>
              ) : (
                <View className="gap-2">
                  {data.contributingReports.slice(0, 8).map((report) => (
                    <Pressable
                      key={report.id}
                      onPress={() => {
                        dismiss();
                        router.push({
                          pathname: '/reports/[id]',
                          params: { id: report.id },
                        });
                      }}
                      style={({ pressed }) => ({ opacity: pressed ? 0.85 : 1 })}
                    >
                      <View className="flex-row items-center gap-3 rounded-2xl border border-border bg-surface p-2">
                        <Image
                          source={{ uri: report.imageUrl }}
                          style={{ width: 56, height: 56, borderRadius: 12 }}
                          contentFit="cover"
                          transition={200}
                        />
                        <View className="flex-1 gap-0.5">
                          <Text className="text-xs font-semibold text-text" numberOfLines={1}>
                            {report.cropType} · {report.disease ?? 'Unknown'}
                          </Text>
                          <Text className="text-[11px] text-text-muted">
                            {timeAgo(report.createdAt)} · {report.confidence ?? 0}% confidence
                          </Text>
                        </View>
                        <ChevronRight size={16} color={theme.textSubtle} strokeWidth={2} />
                      </View>
                    </Pressable>
                  ))}
                </View>
              )}
            </View>

            {/* Prevention recommendations — derived from contributing reports */}
            {data?.contributingReports[0]?.recommendations.length ? (
              <View className="gap-2">
                <Text className="text-base font-semibold text-text">Prevention guidance</Text>
                <View className="gap-2">
                  {data.contributingReports[0].recommendations
                    .slice(0, 4)
                    .map((rec, idx) => (
                      <View
                        key={idx}
                        className="flex-row items-start gap-3 rounded-2xl border border-border bg-surface p-3"
                      >
                        <View className="mt-0.5 h-8 w-8 items-center justify-center rounded-2xl bg-brand-500/15">
                          <Sparkles
                            size={14}
                            color={palette.brand[300]}
                            strokeWidth={2.2}
                          />
                        </View>
                        <Text className="flex-1 text-xs leading-4 text-text">{rec}</Text>
                      </View>
                    ))}
                </View>
              </View>
            ) : null}
          </BottomSheetScrollView>
        )}
      </BottomSheetModal>
    );
  },
);

function Stat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <View
      style={{
        width: '50%',
        padding: 14,
      }}
    >
      <View className="flex-row items-center gap-1.5">
        {icon}
        <Text className="text-[10px] font-medium uppercase tracking-wider text-text-subtle">
          {label}
        </Text>
      </View>
      <Text className="mt-1 text-base font-bold text-text">{value}</Text>
    </View>
  );
}
