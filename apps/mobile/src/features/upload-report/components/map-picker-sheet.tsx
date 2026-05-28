import { BottomSheetModal, BottomSheetView } from '@gorhom/bottom-sheet';
import * as Haptics from 'expo-haptics';
import { LinearGradient } from 'expo-linear-gradient';
import { Check, X } from 'lucide-react-native';
import { forwardRef, useEffect, useRef, useState } from 'react';
import { Platform, Pressable } from 'react-native';
import MapView, { Marker, type Region } from 'react-native-maps';

import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

import type { ReportLocation } from '../types';

interface MapPickerSheetProps {
  initialLocation: ReportLocation | null;
  onConfirm: (lat: number, lng: number) => void;
}

const DEFAULT_REGION: Region = {
  latitude: 20.5937,
  longitude: 78.9629,
  latitudeDelta: 20,
  longitudeDelta: 20,
};

export const MapPickerSheet = forwardRef<BottomSheetModal, MapPickerSheetProps>(
  function MapPickerSheet({ initialLocation, onConfirm }, ref) {
    const theme = useTheme();
    const [pin, setPin] = useState<{ latitude: number; longitude: number } | null>(null);
    const mapRef = useRef<MapView | null>(null);

    useEffect(() => {
      if (initialLocation) {
        setPin({ latitude: initialLocation.latitude, longitude: initialLocation.longitude });
      }
    }, [initialLocation]);

    const initialRegion: Region = initialLocation
      ? {
          latitude: initialLocation.latitude,
          longitude: initialLocation.longitude,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        }
      : DEFAULT_REGION;

    const dismiss = () => {
      // @ts-expect-error: ref provided
      ref?.current?.dismiss();
    };

    const handleConfirm = () => {
      if (!pin) return;
      Haptics.selectionAsync().catch(() => undefined);
      onConfirm(pin.latitude, pin.longitude);
      dismiss();
    };

    return (
      <BottomSheetModal
        ref={ref}
        snapPoints={['90%']}
        backgroundStyle={{ backgroundColor: theme.surfaceElevated }}
        handleIndicatorStyle={{ backgroundColor: theme.borderStrong }}
      >
        <BottomSheetView style={{ flex: 1 }}>
          <View className="flex-row items-center justify-between px-5 pb-3 pt-1">
            <View className="flex-1 gap-0.5">
              <Text className="text-xl font-bold text-text">Pick the location</Text>
              <Text className="text-xs text-text-muted">
                Drag the pin to mark your crop&apos;s exact location.
              </Text>
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Close"
              onPress={dismiss}
              className="h-9 w-9 items-center justify-center rounded-full bg-surface"
            >
              <X size={18} color={theme.text} strokeWidth={2} />
            </Pressable>
          </View>

          <View className="mx-5 flex-1 overflow-hidden rounded-2xl border border-border bg-surface">
            <MapView
              ref={(r) => {
                mapRef.current = r;
              }}
              style={{ flex: 1 }}
              initialRegion={initialRegion}
              onPress={(e) => {
                const c = e.nativeEvent.coordinate;
                setPin({ latitude: c.latitude, longitude: c.longitude });
                Haptics.selectionAsync().catch(() => undefined);
              }}
            >
              {pin ? (
                <Marker
                  coordinate={pin}
                  draggable
                  onDragEnd={(e) => {
                    const c = e.nativeEvent.coordinate;
                    setPin({ latitude: c.latitude, longitude: c.longitude });
                  }}
                  pinColor={palette.brand[600]}
                />
              ) : null}
            </MapView>
          </View>

          {pin ? (
            <View className="px-5 pt-3">
              <Text className="text-center text-xs text-text-muted">
                {pin.latitude.toFixed(5)}, {pin.longitude.toFixed(5)}
              </Text>
            </View>
          ) : null}

          <View className="px-5 pb-6 pt-3">
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Use this location"
              onPress={handleConfirm}
              disabled={!pin}
              style={({ pressed }) => ({
                opacity: !pin ? 0.5 : pressed ? 0.92 : 1,
                borderRadius: 16,
                overflow: 'hidden',
              })}
            >
              <LinearGradient
                colors={[palette.brand[500], palette.brand[600]]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View className="h-12 flex-row items-center justify-center gap-2">
                  <Check size={18} color="#fff" strokeWidth={2.4} />
                  <Text className="text-sm font-semibold text-white">Use this location</Text>
                </View>
              </LinearGradient>
            </Pressable>
            {Platform.OS === 'android' ? (
              <Text className="mt-2 text-center text-[11px] text-text-subtle">
                Map uses Google Maps · location data stays on your device
              </Text>
            ) : null}
          </View>
        </BottomSheetView>
      </BottomSheetModal>
    );
  },
);
