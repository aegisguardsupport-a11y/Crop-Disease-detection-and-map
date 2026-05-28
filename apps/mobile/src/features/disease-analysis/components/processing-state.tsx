import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { Activity } from 'lucide-react-native';
import { useEffect } from 'react';
import Animated, {
  cancelAnimation,
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated';

import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

interface ProcessingStateProps {
  imageUrl: string;
  cropType: string;
}

export function ProcessingState({ imageUrl, cropType }: ProcessingStateProps) {
  const scanY = useSharedValue(0);
  const pulse = useSharedValue(0);

  useEffect(() => {
    scanY.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 1600, easing: Easing.inOut(Easing.ease) }),
        withTiming(0, { duration: 1600, easing: Easing.inOut(Easing.ease) }),
      ),
      -1,
    );
    pulse.value = withRepeat(
      withTiming(1, { duration: 1200, easing: Easing.inOut(Easing.ease) }),
      -1,
      true,
    );
    return () => {
      cancelAnimation(scanY);
      cancelAnimation(pulse);
    };
  }, [scanY, pulse]);

  const scanStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: scanY.value * 220 }],
    opacity: 0.9,
  }));

  const pulseStyle = useAnimatedStyle(() => ({
    opacity: 0.5 + pulse.value * 0.5,
  }));

  return (
    <View className="gap-4">
      <View className="aspect-square w-full overflow-hidden rounded-2xl border border-border bg-surface">
        <Image
          source={{ uri: imageUrl }}
          style={{ width: '100%', height: '100%' }}
          contentFit="cover"
          transition={250}
          cachePolicy="memory-disk"
        />

        {/* soft brand wash so the scan line is more readable */}
        <View
          className="absolute inset-0"
          style={{ backgroundColor: 'rgba(255,255,255,0.18)' }}
        />

        {/* horizontal scan line */}
        <Animated.View
          style={[
            {
              position: 'absolute',
              left: 0,
              right: 0,
              top: 0,
              height: 60,
            },
            scanStyle,
          ]}
        >
          <LinearGradient
            colors={['transparent', `${palette.brand[500]}aa`, 'transparent']}
            style={{ flex: 1 }}
          />
          <View
            className="absolute left-0 right-0"
            style={{
              top: 30,
              height: 1.5,
              backgroundColor: palette.brand[600],
            }}
          />
        </Animated.View>

        {/* corners */}
        <View
          className="absolute"
          style={{
            top: 16,
            left: 16,
            width: 24,
            height: 24,
            borderTopWidth: 2,
            borderLeftWidth: 2,
            borderColor: palette.brand[600],
            borderTopLeftRadius: 8,
          }}
        />
        <View
          className="absolute"
          style={{
            top: 16,
            right: 16,
            width: 24,
            height: 24,
            borderTopWidth: 2,
            borderRightWidth: 2,
            borderColor: palette.brand[600],
            borderTopRightRadius: 8,
          }}
        />
        <View
          className="absolute"
          style={{
            bottom: 16,
            left: 16,
            width: 24,
            height: 24,
            borderBottomWidth: 2,
            borderLeftWidth: 2,
            borderColor: palette.brand[600],
            borderBottomLeftRadius: 8,
          }}
        />
        <View
          className="absolute"
          style={{
            bottom: 16,
            right: 16,
            width: 24,
            height: 24,
            borderBottomWidth: 2,
            borderRightWidth: 2,
            borderColor: palette.brand[600],
            borderBottomRightRadius: 8,
          }}
        />

        {/* light status pill */}
        <View className="absolute left-0 right-0 items-center" style={{ bottom: 20 }}>
          <View className="flex-row items-center gap-2 rounded-full border border-border bg-surface px-4 py-2">
            <Animated.View
              style={[
                {
                  width: 8,
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: palette.brand[500],
                },
                pulseStyle,
              ]}
            />
            <Text className="text-xs font-bold uppercase tracking-[1.2px] text-brand-700">
              Analyzing
            </Text>
          </View>
        </View>
      </View>

      <CyclingMessage cropType={cropType} />
    </View>
  );
}

function CyclingMessage({ cropType }: { cropType: string }) {
  const opacity = useSharedValue(1);

  useEffect(() => {
    opacity.value = withRepeat(
      withSequence(
        withTiming(0.4, { duration: 800, easing: Easing.inOut(Easing.ease) }),
        withTiming(1, { duration: 800, easing: Easing.inOut(Easing.ease) }),
      ),
      -1,
    );
    return () => cancelAnimation(opacity);
  }, [opacity]);

  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));

  return (
    <View className="items-center gap-2">
      <Animated.View style={style} className="flex-row items-center gap-2">
        <Activity size={16} color={palette.brand[600]} strokeWidth={2.4} />
        <Text className="text-base font-bold text-text">
          Analyzing your {cropType.toLowerCase()}
        </Text>
      </Animated.View>
      <Text className="text-center text-xs text-text-muted">
        Our AI is comparing this photo against thousands of disease patterns. This usually takes
        a few seconds.
      </Text>
    </View>
  );
}
