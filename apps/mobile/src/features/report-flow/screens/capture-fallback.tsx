import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { Camera as CameraIcon, Image as ImageIcon, X } from 'lucide-react-native';
import { Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

import type { CapturedImage } from '../types';

interface Props {
  onCaptured: (image: CapturedImage) => void;
  onCancel: () => void;
}

const PICKER_OPTIONS: ImagePicker.ImagePickerOptions = {
  mediaTypes: ImagePicker.MediaTypeOptions.Images,
  allowsEditing: true,
  aspect: [1, 1],
  quality: 0.85,
};

/**
 * Camera-free fallback for the capture step. Used when the in-page
 * `expo-camera` preview can't load — most commonly when the dev client was
 * built before `expo-camera` was installed (a rebuild is required for the
 * embedded camera). This path relies only on `expo-image-picker`, which is
 * always available in the JS bundle, so the report flow still works.
 */
export function CaptureFallbackScreen({ onCaptured, onCancel }: Props) {
  const launch = async (mode: 'camera' | 'library') => {
    if (mode === 'camera') {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (!perm.granted) return;
    } else {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) return;
    }
    const result =
      mode === 'camera'
        ? await ImagePicker.launchCameraAsync(PICKER_OPTIONS)
        : await ImagePicker.launchImageLibraryAsync(PICKER_OPTIONS);
    if (result.canceled || !result.assets[0]) return;
    const a = result.assets[0];
    onCaptured({ uri: a.uri, width: a.width, height: a.height });
  };

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top', 'bottom']} style={{ flex: 1 }}>
        <View className="flex-row items-center justify-between px-4 py-2">
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Close"
            onPress={() => {
              onCancel();
              router.back();
            }}
            className="h-10 w-10 items-center justify-center rounded-full border border-border bg-surface"
          >
            <X size={18} color={palette.brand[700]} strokeWidth={2.2} />
          </Pressable>
          <Text className="text-xs font-bold uppercase tracking-[1.4px] text-brand-700">
            Step 1 of 4
          </Text>
          <View className="h-10 w-10" />
        </View>

        <View className="flex-1 items-center justify-center gap-4 px-8">
          <View className="h-20 w-20 items-center justify-center rounded-3xl bg-brand-50">
            <CameraIcon size={36} color={palette.brand[600]} strokeWidth={2} />
          </View>
          <Text className="text-center text-lg font-bold text-text">Add a crop photo</Text>
          <Text className="text-center text-sm text-text-muted">
            Take a photo of the affected leaf or choose an existing one from your gallery.
          </Text>
        </View>

        <View className="gap-2 px-4 pb-4">
          <Button
            label="Take a photo"
            variant="gradient"
            size="lg"
            leftSlot={<CameraIcon size={18} color="#ffffff" strokeWidth={2.2} />}
            onPress={() => void launch('camera')}
          />
          <Button
            label="Choose from gallery"
            variant="ghost"
            size="lg"
            leftSlot={<ImageIcon size={18} color={palette.brand[700]} strokeWidth={2.2} />}
            onPress={() => void launch('library')}
          />
        </View>
      </SafeAreaView>
    </View>
  );
}
