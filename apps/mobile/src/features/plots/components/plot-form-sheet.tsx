import {
  BottomSheetBackdrop,
  BottomSheetModal,
  BottomSheetScrollView,
  BottomSheetTextInput,
} from '@gorhom/bottom-sheet';
import { Crosshair, MapPin, Trash2, X } from 'lucide-react-native';
import { forwardRef, useEffect, useState } from 'react';
import { Pressable } from 'react-native';

import { Button } from '@/components/ui/button';
import { CROPS } from '@/constants/crops';
import { useCurrentLocation } from '@/features/upload-report/hooks/use-current-location';
import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

import type { Plot } from '../api/plots.api';
import { useCreatePlot, useDeletePlot, useUpdatePlot } from '../hooks/use-plots';

interface PlotFormSheetProps {
  /** When provided, sheet acts as edit mode. */
  plot?: Plot | null;
  onSaved?: (plot: Plot) => void;
  onDeleted?: () => void;
  onOpenMapPicker?: (current: { lat: number; lng: number } | null) => void;
}

export const PlotFormSheet = forwardRef<BottomSheetModal, PlotFormSheetProps>(
  function PlotFormSheet({ plot, onSaved, onDeleted, onOpenMapPicker }, ref) {
    const theme = useTheme();
    const isEdit = !!plot;
    const [name, setName] = useState(plot?.name ?? '');
    const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(
      plot ? { lat: plot.latitude, lng: plot.longitude } : null,
    );
    const [crops, setCrops] = useState<string[]>(plot?.cropTypes ?? []);
    const [error, setError] = useState<string | null>(null);

    const locationCtl = useCurrentLocation(false);

    const create = useCreatePlot();
    const update = useUpdatePlot();
    const remove = useDeletePlot();

    /* eslint-disable react-hooks/set-state-in-effect */
    // Reset form whenever the plot prop changes (edit different plot, etc).
    useEffect(() => {
      setName(plot?.name ?? '');
      setCoords(plot ? { lat: plot.latitude, lng: plot.longitude } : null);
      setCrops(plot?.cropTypes ?? []);
      setError(null);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [plot?.id]);
    /* eslint-enable react-hooks/set-state-in-effect */

    const dismiss = () => {
      // @ts-expect-error: ref provided
      ref?.current?.dismiss();
    };

    const handleUseGps = async () => {
      await locationCtl.refresh();
      if (locationCtl.location) {
        setCoords({ lat: locationCtl.location.latitude, lng: locationCtl.location.longitude });
      }
    };

    // If location resolves after refresh
    useEffect(() => {
      if (locationCtl.location && !coords) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setCoords({ lat: locationCtl.location.latitude, lng: locationCtl.location.longitude });
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [locationCtl.location]);

    const toggleCrop = (cropName: string) => {
      setCrops((prev) =>
        prev.includes(cropName) ? prev.filter((c) => c !== cropName) : [...prev, cropName],
      );
    };

    const isPending = create.isPending || update.isPending;

    const handleSave = async () => {
      setError(null);
      if (!name.trim()) return setError('Give your plot a name.');
      if (!coords) return setError('Set the plot location.');
      try {
        if (isEdit && plot) {
          const next = await update.mutateAsync({
            id: plot.id,
            payload: {
              name: name.trim(),
              latitude: coords.lat,
              longitude: coords.lng,
              cropTypes: crops,
            },
          });
          onSaved?.(next);
        } else {
          const next = await create.mutateAsync({
            name: name.trim(),
            latitude: coords.lat,
            longitude: coords.lng,
            cropTypes: crops,
          });
          onSaved?.(next);
        }
        dismiss();
      } catch (err) {
        setError((err as Error).message ?? 'Could not save plot');
      }
    };

    const handleDelete = async () => {
      if (!plot) return;
      try {
        await remove.mutateAsync(plot.id);
        onDeleted?.();
        dismiss();
      } catch (err) {
        setError((err as Error).message ?? 'Could not delete plot');
      }
    };

    return (
      <BottomSheetModal
        ref={ref}
        snapPoints={['85%']}
        backgroundStyle={{
          backgroundColor: '#ffffff',
          borderTopLeftRadius: 24,
          borderTopRightRadius: 24,
        }}
        handleIndicatorStyle={{ backgroundColor: '#e8e4dc', width: 36 }}
        backdropComponent={(props) => (
          <BottomSheetBackdrop
            {...props}
            disappearsOnIndex={-1}
            appearsOnIndex={0}
            opacity={0.5}
          />
        )}
        keyboardBehavior="interactive"
        keyboardBlurBehavior="restore"
      >
        <View className="flex-row items-center justify-between px-5 pb-3 pt-1">
          <Text className="text-xl font-bold text-text">
            {isEdit ? 'Edit plot' : 'Add a plot'}
          </Text>
          <Pressable
            accessibilityRole="button"
            onPress={dismiss}
            className="h-9 w-9 items-center justify-center rounded-full border border-border bg-surface"
          >
            <X size={18} color={theme.text} strokeWidth={2} />
          </Pressable>
        </View>

        <BottomSheetScrollView contentContainerStyle={{ padding: 20, gap: 16, paddingBottom: 80 }}>
          <Section label="Plot name">
            <View className="rounded-xl border border-border bg-surface px-3">
              <BottomSheetTextInput
                value={name}
                onChangeText={setName}
                placeholder="e.g. North field"
                placeholderTextColor={theme.textFaint}
                style={{ height: 48, color: theme.text, fontSize: 15 }}
              />
            </View>
          </Section>

          <Section label="Location">
            <View className="gap-2">
              <View className="rounded-xl border border-border bg-surface p-3">
                <View className="flex-row items-center gap-2">
                  <MapPin size={16} color={palette.brand[700]} strokeWidth={2.2} />
                  <Text className="flex-1 text-sm text-text">
                    {coords
                      ? `${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}`
                      : 'No location set'}
                  </Text>
                </View>
              </View>
              <View className="flex-row gap-2">
                <View className="flex-1">
                  <Button
                    label={locationCtl.status === 'fetching' ? 'Locating…' : 'Use my GPS'}
                    variant="solid"
                    size="sm"
                    onPress={handleUseGps}
                    disabled={
                      locationCtl.status === 'fetching' ||
                      locationCtl.status === 'requesting'
                    }
                    leftSlot={
                      <Crosshair
                        size={14}
                        color={theme.text}
                        strokeWidth={2.2}
                      />
                    }
                  />
                </View>
                <View className="flex-1">
                  <Button
                    label="Pick on map"
                    variant="ghost"
                    size="sm"
                    onPress={() => onOpenMapPicker?.(coords)}
                    leftSlot={
                      <MapPin
                        size={14}
                        color={palette.brand[600]}
                        strokeWidth={2.2}
                      />
                    }
                  />
                </View>
              </View>
            </View>
          </Section>

          <Section label="Crops grown here (optional)">
            <View className="flex-row flex-wrap gap-2">
              {CROPS.map((c) => {
                const selected = crops.includes(c.name);
                return (
                  <Pressable
                    key={c.id}
                    accessibilityRole="button"
                    onPress={() => toggleCrop(c.name)}
                    style={({ pressed }) => ({ opacity: pressed ? 0.85 : 1 })}
                  >
                    <View
                      className={`rounded-full border px-3 py-1.5 ${
                        selected
                          ? 'border-brand-600 bg-brand-50'
                          : 'border-border bg-surface'
                      }`}
                    >
                      <Text
                        className={`text-xs font-bold ${
                          selected ? 'text-brand-700' : 'text-text-muted'
                        }`}
                      >
                        {c.emoji} {c.name}
                      </Text>
                    </View>
                  </Pressable>
                );
              })}
            </View>
          </Section>

          {error ? (
            <View className="rounded-xl border border-danger-tint bg-danger-tint px-3 py-2">
              <Text className="text-xs font-medium text-danger">{error}</Text>
            </View>
          ) : null}
        </BottomSheetScrollView>

        <View className="flex-row items-center gap-2 border-t border-border bg-surface px-5 py-4">
          {isEdit ? (
            <Pressable
              accessibilityRole="button"
              onPress={handleDelete}
              disabled={remove.isPending}
              style={({ pressed }) => ({ opacity: pressed ? 0.7 : 1 })}
            >
              <View className="h-12 w-12 items-center justify-center rounded-xl border border-danger-tint bg-danger-tint">
                <Trash2 size={16} color={theme.danger} strokeWidth={2.2} />
              </View>
            </Pressable>
          ) : null}
          <View className="flex-1">
            <Button
              label={isEdit ? 'Save changes' : 'Add plot'}
              variant="gradient"
              size="md"
              loading={isPending}
              onPress={handleSave}
            />
          </View>
        </View>
      </BottomSheetModal>
    );
  },
);

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View className="gap-2">
      <Text className="text-[11px] font-bold uppercase tracking-[1.4px] text-text-subtle">
        {label}
      </Text>
      {children}
    </View>
  );
}
