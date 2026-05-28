import { GlassView } from 'expo-glass-effect';
import { Image } from 'expo-image';
import { CloudOff, RefreshCw, Trash2 } from 'lucide-react-native';
import { Platform, Pressable } from 'react-native';

import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';
import { timeAgo } from '@/utils/severity';

import { useOfflineQueueStore } from '../store/offline-queue.store';

export function PendingUploadsSection() {
  const theme = useTheme();
  const items = useOfflineQueueStore((s) => s.items);
  const remove = useOfflineQueueStore((s) => s.remove);
  const update = useOfflineQueueStore((s) => s.update);

  if (items.length === 0) return null;

  return (
    <View className="gap-3">
      <View className="flex-row items-center gap-2 px-1">
        <CloudOff size={16} color={theme.textMuted} strokeWidth={2.2} />
        <Text className="text-xs font-medium uppercase tracking-wider text-text-muted">
          Pending uploads · {items.length}
        </Text>
      </View>

      {items.map((item) => (
        <GlassView
          key={item.id}
          glassEffectStyle="regular"
          tintColor={Platform.OS === 'ios' ? `${theme.surfaceElevated}AA` : theme.surfaceElevated}
          style={{ borderRadius: 20, overflow: 'hidden' }}
        >
          <View className="flex-row items-center gap-3 rounded-[20px] border border-border p-3">
            <View className="h-12 w-12 overflow-hidden rounded-xl bg-surface">
              <Image
                source={{ uri: item.draft.localImageUri }}
                style={{ width: '100%', height: '100%' }}
                contentFit="cover"
              />
            </View>
            <View className="flex-1 gap-0.5">
              <Text className="text-sm font-semibold text-text">{item.draft.cropTypeName}</Text>
              <Text
                className={`text-[11px] ${
                  item.status === 'failed' ? 'text-danger' : 'text-text-muted'
                }`}
                numberOfLines={1}
              >
                {item.status === 'failed'
                  ? `Failed · ${item.lastError ?? 'will retry later'}`
                  : item.status === 'uploading'
                    ? 'Uploading…'
                    : `Queued · ${timeAgo(item.createdAt)}`}
              </Text>
            </View>

            <View className="flex-row gap-1">
              {item.status === 'failed' ? (
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Retry"
                  onPress={() => {
                    void update(item.id, {
                      status: 'pending',
                      attempts: 0,
                      nextAttemptAt: undefined,
                    });
                  }}
                  className="h-9 w-9 items-center justify-center rounded-xl bg-surface"
                >
                  <RefreshCw size={14} color={palette.brand[400]} strokeWidth={2.2} />
                </Pressable>
              ) : null}
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Discard"
                onPress={() => {
                  void remove(item.id);
                }}
                className="h-9 w-9 items-center justify-center rounded-xl bg-surface"
              >
                <Trash2 size={14} color={theme.danger} strokeWidth={2.2} />
              </Pressable>
            </View>
          </View>
        </GlassView>
      ))}
    </View>
  );
}
