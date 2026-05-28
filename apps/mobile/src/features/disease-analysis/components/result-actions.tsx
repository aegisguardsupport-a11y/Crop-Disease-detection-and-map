import * as Haptics from 'expo-haptics';
import { Map, Plus, Share2 } from 'lucide-react-native';
import { Share } from 'react-native';

import { PressableScale } from '@/components/ui/pressable-scale';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';
import type { Report } from '@/features/upload-report/types';

interface ResultActionsProps {
  report: Report;
  onUploadAnother: () => void;
  onViewOnMap: () => void;
}

export function ResultActions({ report, onUploadAnother, onViewOnMap }: ResultActionsProps) {
  const handleShare = async () => {
    await Haptics.selectionAsync().catch(() => undefined);
    try {
      await Share.share({
        message: `Crop diagnosis from AgroRadar\n\n${report.cropType} · ${
          report.disease ?? 'unknown'
        } (${report.confidence ?? 0}% confidence)\n\nReport ID: ${report.id}`,
        title: 'Crop disease report',
      });
    } catch {
      /* noop */
    }
  };

  return (
    <View className="flex-row items-stretch gap-2">
      <ActionButton
        icon={<Map size={18} color={palette.brand[700]} strokeWidth={2.2} />}
        label="View on map"
        onPress={() => {
          Haptics.selectionAsync().catch(() => undefined);
          onViewOnMap();
        }}
      />
      <ActionButton
        icon={<Share2 size={18} color={palette.brand[700]} strokeWidth={2.2} />}
        label="Share"
        onPress={handleShare}
      />
      <ActionButton
        icon={<Plus size={18} color={palette.brand[700]} strokeWidth={2.2} />}
        label="New report"
        onPress={() => {
          Haptics.selectionAsync().catch(() => undefined);
          onUploadAnother();
        }}
      />
    </View>
  );
}

function ActionButton({
  icon,
  label,
  onPress,
}: {
  icon: React.ReactNode;
  label: string;
  onPress: () => void;
}) {
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      haptic="none"
      pressedScale={0.96}
      className="flex-1"
    >
      <View className="items-center gap-1.5 rounded-2xl border border-border bg-surface px-3 py-3">
        {icon}
        <Text className="text-[11px] font-bold text-text" numberOfLines={1}>
          {label}
        </Text>
      </View>
    </PressableScale>
  );
}
