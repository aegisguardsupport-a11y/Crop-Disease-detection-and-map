import {
  CameraView,
  useCameraPermissions,
  type CameraCapturedPicture,
} from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { Camera as CameraIcon, Image as ImageIcon, X, Zap, ZapOff } from 'lucide-react-native';
import { useRef, useState } from 'react';
import { ActivityIndicator, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { PressableScale } from '@/components/ui/pressable-scale';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

import type { CapturedImage } from '../types';

interface Props {
  onCaptured: (image: CapturedImage) => void;
  onCancel: () => void;
}

/** Flash modes we cycle through with the toggle button: off → auto → on → off. */
const FLASH_CYCLE = ['off', 'auto', 'on'] as const;
type CycledFlash = (typeof FLASH_CYCLE)[number];

const FLASH_LABEL: Record<CycledFlash, string> = {
  off: 'Off',
  auto: 'Auto',
  on: 'On',
};

/**
 * Step 1 of the report flow. Renders a live in-page camera preview
 * (expo-camera `CameraView`) with a shutter button, a flash-mode toggle,
 * and a gallery picker. Falls back to a permission-request screen when
 * camera access has not been granted yet.
 */
export function CaptureScreen({ onCaptured, onCancel }: Props) {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const [flash, setFlash] = useState<CycledFlash>('off');
  const [isReady, setIsReady] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);

  const close = () => {
    onCancel();
    router.back();
  };

  const handleCapture = async () => {
    if (!isReady || isCapturing) return;
    setIsCapturing(true);
    try {
      const photo: CameraCapturedPicture | undefined = await cameraRef.current?.takePictureAsync({
        quality: 0.85,
      });
      if (photo?.uri) {
        onCaptured({ uri: photo.uri, width: photo.width, height: photo.height });
      }
    } finally {
      setIsCapturing(false);
    }
  };

  const handleGallery = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) return;
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.85,
    });
    if (result.canceled || !result.assets[0]) return;
    const a = result.assets[0];
    onCaptured({ uri: a.uri, width: a.width, height: a.height });
  };

  // Permissions still resolving on first mount.
  if (!permission) {
    return (
      <View className="flex-1 items-center justify-center bg-bg">
        <ActivityIndicator color={palette.brand[600]} />
      </View>
    );
  }

  // Permission not granted yet — show a friendly request screen.
  if (!permission.granted) {
    return (
      <View className="flex-1 bg-bg">
        <SafeAreaView edges={['top', 'bottom']} style={{ flex: 1 }}>
          <View className="flex-row items-center justify-between px-4 py-2">
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Close"
              onPress={close}
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
            <Text className="text-center text-lg font-bold text-text">
              Camera access needed
            </Text>
            <Text className="text-center text-sm text-text-muted">
              AgroRadar uses your camera to photograph crops for disease analysis. You can also
              pick an existing photo from your gallery.
            </Text>
            <View className="mt-2 w-full gap-2">
              {permission.canAskAgain ? (
                <Button label="Allow camera" variant="gradient" onPress={() => void requestPermission()} />
              ) : null}
              <Button label="Choose from gallery" variant="ghost" onPress={() => void handleGallery()} />
            </View>
          </View>
        </SafeAreaView>
      </View>
    );
  }

  // Permission granted — live camera preview with controls overlay.
  return (
    <View className="flex-1 bg-black">
      <CameraView
        ref={cameraRef}
        style={{ flex: 1 }}
        facing="back"
        flash={flash}
        onCameraReady={() => setIsReady(true)}
      />

      {/* Controls overlay */}
      <SafeAreaView
        edges={['top', 'bottom']}
        pointerEvents="box-none"
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
      >
        {/* Top bar */}
        <View className="flex-row items-center justify-between px-4 py-2">
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Close"
            onPress={close}
            className="h-10 w-10 items-center justify-center rounded-full"
            style={{ backgroundColor: 'rgba(0,0,0,0.45)' }}
          >
            <X size={18} color="#ffffff" strokeWidth={2.4} />
          </Pressable>
          <View className="rounded-full px-3 py-1" style={{ backgroundColor: 'rgba(0,0,0,0.45)' }}>
            <Text className="text-xs font-bold uppercase tracking-[1.4px] text-white">
              Step 1 of 4
            </Text>
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Flash ${FLASH_LABEL[flash]}`}
            onPress={() =>
              setFlash((f) => FLASH_CYCLE[(FLASH_CYCLE.indexOf(f) + 1) % FLASH_CYCLE.length])
            }
            className="h-10 w-10 items-center justify-center rounded-full"
            style={{ backgroundColor: flash === 'off' ? 'rgba(0,0,0,0.45)' : palette.brand[600] }}
          >
            {flash === 'off' ? (
              <ZapOff size={18} color="#ffffff" strokeWidth={2.4} />
            ) : (
              <Zap size={18} color="#ffffff" strokeWidth={2.4} fill="#ffffff" />
            )}
          </Pressable>
        </View>

        {/* Spacer pushes controls to the bottom */}
        <View className="flex-1" />

        {/* Framing hint */}
        <View className="items-center pb-3">
          <View className="rounded-full px-3 py-1.5" style={{ backgroundColor: 'rgba(0,0,0,0.45)' }}>
            <Text className="text-xs font-medium text-white">
              Frame the affected leaf · flash {FLASH_LABEL[flash]}
            </Text>
          </View>
        </View>

        {/* Bottom control row */}
        <View className="flex-row items-center justify-around px-8 pb-2">
          <PressableScale
            accessibilityRole="button"
            accessibilityLabel="Choose from gallery"
            onPress={() => void handleGallery()}
            haptic="selection"
            className="h-12 w-12 items-center justify-center rounded-full"
            style={{ backgroundColor: 'rgba(0,0,0,0.45)' }}
          >
            <ImageIcon size={22} color="#ffffff" strokeWidth={2.2} />
          </PressableScale>

          <PressableScale
            accessibilityRole="button"
            accessibilityLabel="Capture photo"
            onPress={() => void handleCapture()}
            haptic="medium"
            pressedScale={0.92}
            disabled={!isReady || isCapturing}
            className="h-[78px] w-[78px] items-center justify-center rounded-full"
            style={{ backgroundColor: 'rgba(255,255,255,0.25)' }}
          >
            <View
              className="h-16 w-16 items-center justify-center rounded-full border-[3px]"
              style={{ borderColor: '#ffffff', backgroundColor: '#ffffff' }}
            >
              {isCapturing ? <ActivityIndicator color={palette.brand[600]} /> : null}
            </View>
          </PressableScale>

          {/* Symmetry spacer to keep the shutter centered */}
          <View className="h-12 w-12" />
        </View>
      </SafeAreaView>
    </View>
  );
}
