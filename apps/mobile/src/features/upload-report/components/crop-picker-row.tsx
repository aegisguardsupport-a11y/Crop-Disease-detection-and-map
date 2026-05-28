import { GlassView } from 'expo-glass-effect';
import { ChevronRight, Leaf } from 'lucide-react-native';
import { Platform } from 'react-native';

import { PressableScale } from '@/components/ui/pressable-scale';
import { CROP_BY_ID, type Crop } from '@/constants/crops';
import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

interface CropPickerRowProps {
  cropId: string | null;
  onPress: () => void;
  error?: string;
}

export function CropPickerRow({ cropId, onPress, error }: CropPickerRowProps) {
  const theme = useTheme();
  const crop: Crop | undefined = cropId ? CROP_BY_ID[cropId] : undefined;

  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel="Choose crop type"
      onPress={onPress}
      pressedScale={0.98}
    >
      <GlassView
        glassEffectStyle="regular"
        tintColor={Platform.OS === 'ios' ? `${theme.surfaceElevated}AA` : theme.surfaceElevated}
        style={{ borderRadius: 20, overflow: 'hidden' }}
      >
        <View
          className={`flex-row items-center gap-3 rounded-[20px] border p-3 ${
            error ? 'border-danger/40' : 'border-border'
          }`}
        >
          <View className="h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/15">
            {crop ? (
              <Text className="text-2xl">{crop.emoji}</Text>
            ) : (
              <Leaf size={22} color={palette.brand[300]} strokeWidth={2.2} />
            )}
          </View>

          <View className="flex-1 gap-0.5">
            <Text className="text-[11px] font-medium uppercase tracking-wider text-text-subtle">
              Crop
            </Text>
            <Text className="text-base font-semibold text-text">
              {crop?.name ?? 'Choose crop'}
            </Text>
            {error ? <Text className="text-xs text-danger">{error}</Text> : null}
          </View>

          <ChevronRight size={20} color={theme.textSubtle} strokeWidth={2} />
        </View>
      </GlassView>
    </PressableScale>
  );
}
