import { GlassView } from 'expo-glass-effect';
import { Platform } from 'react-native';

import { useTheme } from '@/hooks/use-theme';
import { Text, TextInput, View } from '@/tw';

const MAX = 500;

interface NotesInputProps {
  value: string;
  onChangeText: (value: string) => void;
}

export function NotesInput({ value, onChangeText }: NotesInputProps) {
  const theme = useTheme();
  const handleChange = (next: string) => {
    if (next.length <= MAX) onChangeText(next);
  };

  return (
    <GlassView
      glassEffectStyle="regular"
      tintColor={Platform.OS === 'ios' ? `${theme.surfaceElevated}AA` : theme.surfaceElevated}
      style={{ borderRadius: 20, overflow: 'hidden' }}
    >
      <View className="gap-2 rounded-[20px] border border-border p-3">
        <View className="flex-row items-center justify-between">
          <Text className="text-[11px] font-medium uppercase tracking-wider text-text-subtle">
            Notes (optional)
          </Text>
          <Text className="text-[11px] text-text-subtle">
            {value.length}/{MAX}
          </Text>
        </View>
        <TextInput
          value={value}
          onChangeText={handleChange}
          placeholder="Anything that might help with diagnosis — e.g. 'lower leaves curled and yellowing for 3 days'."
          placeholderTextColor={theme.textSubtle}
          multiline
          textAlignVertical="top"
          style={{
            minHeight: 84,
            color: theme.text,
            fontSize: 15,
            lineHeight: 22,
          }}
        />
      </View>
    </GlassView>
  );
}
