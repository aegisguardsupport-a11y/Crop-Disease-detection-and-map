import { LinearGradient } from 'expo-linear-gradient';
import { forwardRef } from 'react';
import { ActivityIndicator } from 'react-native';

import { PressableScale } from '@/components/ui/pressable-scale';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';
import { cn } from '@/utils/cn';

type Variant = 'gradient' | 'solid' | 'ghost' | 'destructive';
type Size = 'sm' | 'md' | 'lg';

const sizeContainer: Record<Size, string> = {
  sm: 'h-10 px-4 rounded-xl',
  md: 'h-12 px-5 rounded-xl',
  lg: 'h-14 px-6 rounded-2xl',
};

const sizeLabel: Record<Size, string> = {
  sm: 'text-sm font-bold',
  md: 'text-base font-bold',
  lg: 'text-base font-bold',
};

export interface ButtonProps {
  label: string;
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  disabled?: boolean;
  onPress?: () => void;
  leftSlot?: React.ReactNode;
  rightSlot?: React.ReactNode;
  className?: string;
  haptic?: boolean;
  fullWidth?: boolean;
  testID?: string;
}

/**
 * Soft Sage button.
 * - `gradient` (default) — emerald→teal gradient with brand shadow. Primary CTA.
 * - `ghost` — white with brand-tint border + brand-teal text.
 * - `solid` — solid surface, dark text. For neutral confirmations.
 * - `destructive` — danger background, white text.
 */
export const Button = forwardRef<React.ComponentRef<typeof PressableScale>, ButtonProps>(
  function Button(
    {
      label,
      variant = 'gradient',
      size = 'md',
      loading = false,
      disabled = false,
      onPress,
      leftSlot,
      rightSlot,
      className,
      haptic = true,
      fullWidth = true,
      testID,
    },
    ref,
  ) {
    const isDisabled = disabled || loading;
    const hapticIntensity = !haptic
      ? 'none'
      : variant === 'destructive'
        ? 'medium'
        : variant === 'gradient'
          ? 'light'
          : 'selection';
    const labelTone =
      variant === 'gradient' || variant === 'destructive'
        ? 'text-white'
        : variant === 'ghost'
          ? 'text-brand-600'
          : 'text-text';

    const containerBase = cn(
      'flex-row items-center justify-center gap-2 overflow-hidden',
      sizeContainer[size],
      fullWidth && 'self-stretch',
      isDisabled && 'opacity-60',
      className,
    );

    const inner = loading ? (
      <ActivityIndicator
        color={
          variant === 'gradient' || variant === 'destructive'
            ? '#fff'
            : palette.brand[600]
        }
      />
    ) : (
      <>
        {leftSlot ? <View className="mr-1">{leftSlot}</View> : null}
        <Text className={cn(sizeLabel[size], labelTone)}>{label}</Text>
        {rightSlot ? <View className="ml-1">{rightSlot}</View> : null}
      </>
    );

    if (variant === 'gradient') {
      return (
        <PressableScale
          ref={ref}
          accessibilityRole="button"
          accessibilityState={{ disabled: isDisabled, busy: loading }}
          disabled={isDisabled}
          onPress={onPress}
          haptic={hapticIntensity}
          pressedScale={size === 'lg' ? 0.97 : 0.96}
          testID={testID}
          className={containerBase}
          style={{
            shadowColor: palette.brand[600],
            shadowOffset: { width: 0, height: 6 },
            shadowOpacity: isDisabled ? 0 : 0.32,
            shadowRadius: 14,
            elevation: isDisabled ? 0 : 6,
          }}
        >
          <LinearGradient
            colors={[palette.brand[500], palette.brand[600]]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={{ position: 'absolute', inset: 0 }}
          />
          {inner}
        </PressableScale>
      );
    }

    const bg =
      variant === 'destructive'
        ? 'bg-danger'
        : variant === 'ghost'
          ? 'border border-brand-200 bg-surface'
          : 'bg-surface border border-border';

    return (
      <PressableScale
        ref={ref}
        accessibilityRole="button"
        accessibilityState={{ disabled: isDisabled, busy: loading }}
        disabled={isDisabled}
        onPress={onPress}
        haptic={hapticIntensity}
        pressedScale={size === 'lg' ? 0.97 : 0.96}
        testID={testID}
        className={cn(containerBase, bg)}
      >
        {inner}
      </PressableScale>
    );
  },
);
