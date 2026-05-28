import { GlassView } from 'expo-glass-effect';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { Camera, ImagePlus, RefreshCw } from 'lucide-react-native';
import { Platform } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';

import { PressableScale } from '@/components/ui/pressable-scale';
import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';
import { cn } from '@/utils/cn';

import type { PickedImage } from '../types';

interface ImagePickerCardProps {
  picked: PickedImage | null;
  onPickCamera: () => void;
  onPickGallery: () => void;
  onClear: () => void;
  className?: string;
}

export function ImagePickerCard({
  picked,
  onPickCamera,
  onPickGallery,
  onClear,
  className,
}: ImagePickerCardProps) {
  const theme = useTheme();

  if (picked) {
    return (
      <Animated.View entering={FadeIn.duration(200)} exiting={FadeOut.duration(150)}>
        <View
          className={cn(
            'overflow-hidden rounded-3xl border border-border bg-surface',
            className,
          )}
        >
          <Image
            source={{ uri: picked.uri }}
            style={{ width: '100%', aspectRatio: 1 }}
            contentFit="cover"
            transition={200}
          />
          <LinearGradient
            colors={['transparent', 'rgba(0,0,0,0.65)']}
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              bottom: 0,
              height: '40%',
            }}
          />
          <View className="absolute bottom-0 left-0 right-0 flex-row items-center justify-between p-4">
            <View>
              <Text className="text-[11px] font-medium uppercase tracking-wider text-white/70">
                Selected photo
              </Text>
              <Text className="text-sm font-semibold text-white">
                {picked.width} × {picked.height}
              </Text>
            </View>
            <View className="flex-row gap-2">
              <PressableScale
                accessibilityRole="button"
                accessibilityLabel="Replace photo"
                onPress={onPickGallery}
                pressedScale={0.9}
                haptic="selection"
                className="h-10 w-10 items-center justify-center rounded-full bg-white/20"
              >
                <RefreshCw size={16} color="#fff" strokeWidth={2.2} />
              </PressableScale>
              <PressableScale
                accessibilityRole="button"
                accessibilityLabel="Remove photo"
                onPress={onClear}
                pressedScale={0.94}
                haptic="medium"
                className="h-10 rounded-full bg-white/20 px-3"
              >
                <View className="h-full items-center justify-center">
                  <Text className="text-xs font-semibold text-white">Remove</Text>
                </View>
              </PressableScale>
            </View>
          </View>
        </View>
      </Animated.View>
    );
  }

  return (
    <GlassView
      glassEffectStyle="regular"
      tintColor={Platform.OS === 'ios' ? `${theme.surfaceElevated}AA` : theme.surfaceElevated}
      style={{ borderRadius: 28, overflow: 'hidden' }}
    >
      <View
        className={cn('rounded-[28px] border border-border p-4', className)}
      >
        <View className="items-center gap-1 py-2">
          <Text className="text-base font-semibold text-text">Add a crop photo</Text>
          <Text className="text-center text-xs text-text-muted">
            Capture a fresh shot or upload from your gallery.
          </Text>
        </View>

        <View className="mt-3 flex-row gap-3">
          <PickerButton
            label="Camera"
            description="Take a photo"
            icon={<Camera size={22} color={palette.brand[300]} strokeWidth={2.2} />}
            onPress={onPickCamera}
          />
          <PickerButton
            label="Gallery"
            description="Pick a photo"
            icon={<ImagePlus size={22} color={palette.brand[300]} strokeWidth={2.2} />}
            onPress={onPickGallery}
          />
        </View>
      </View>
    </GlassView>
  );
}

function PickerButton({
  label,
  description,
  icon,
  onPress,
}: {
  label: string;
  description: string;
  icon: React.ReactNode;
  onPress: () => void;
}) {
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      pressedScale={0.96}
      haptic="light"
      style={{ flex: 1 }}
    >
      <View className="items-center gap-2 rounded-2xl border border-border bg-surface-muted px-3 py-4">
        <View className="h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/15">
          {icon}
        </View>
        <View className="items-center gap-0.5">
          <Text className="text-sm font-semibold text-text">{label}</Text>
          <Text className="text-[11px] text-text-muted">{description}</Text>
        </View>
      </View>
    </PressableScale>
  );
}
