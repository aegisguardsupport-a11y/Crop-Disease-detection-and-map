import { Image } from 'expo-image';

import { palette } from '@/theme/colors';
import { SectionLabel } from '@/components/ui/section-label';
import { Text, View } from '@/tw';
import type { Severity } from '@/features/upload-report/types';

interface ResultHeroProps {
  imageUrl: string;
  cropType: string;
  severity?: Severity | null;
}

const SEVERITY_STRIP: Record<Severity, string> = {
  LOW: palette.status.success,
  MEDIUM: '#d97706',
  HIGH: '#dc2626',
};

export function ResultHero({ imageUrl, cropType, severity }: ResultHeroProps) {
  const stripColor = severity ? SEVERITY_STRIP[severity] : palette.brand[400];

  return (
    <View className="overflow-hidden rounded-2xl border border-border bg-surface">
      <Image
        source={{ uri: imageUrl }}
        style={{ width: '100%', aspectRatio: 1 }}
        contentFit="cover"
        transition={200}
      />

      {/* severity strip on top */}
      <View
        className="absolute left-0 right-0 top-0 h-1.5"
        style={{ backgroundColor: stripColor }}
      />

      {/* corner accent */}
      <View
        className="absolute"
        style={{
          top: 12,
          right: 12,
          paddingHorizontal: 10,
          paddingVertical: 4,
          borderRadius: 999,
          backgroundColor: 'rgba(255,255,255,0.92)',
          borderWidth: 1,
          borderColor: palette.brand[100],
        }}
      >
        <Text className="text-[10px] font-bold uppercase tracking-[1.2px] text-brand-700">
          AI · Diagnosis
        </Text>
      </View>

      <View className="flex-row items-center justify-between gap-3 px-4 py-3">
        <View className="flex-1 gap-0.5">
          <SectionLabel>Crop</SectionLabel>
          <Text className="text-lg font-extrabold tracking-tight text-text" numberOfLines={1}>
            {cropType}
          </Text>
        </View>
        <View
          style={{
            paddingHorizontal: 8,
            paddingVertical: 3,
            borderRadius: 999,
            backgroundColor: palette.brand[50],
            borderWidth: 1,
            borderColor: palette.brand[100],
          }}
        >
          <Text className="text-[10px] font-bold uppercase tracking-[1.2px] text-brand-700">
            Predicted
          </Text>
        </View>
      </View>
    </View>
  );
}
