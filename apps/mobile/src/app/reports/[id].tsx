import { router, useLocalSearchParams } from 'expo-router';
import { ChevronLeft, MoreHorizontal, RefreshCw } from 'lucide-react-native';
import { ScrollView } from 'react-native';
import Animated, { FadeIn, FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loader } from '@/components/ui/loader';
import { PressableScale } from '@/components/ui/pressable-scale';
import { SectionLabel } from '@/components/ui/section-label';
import { ConfidenceRing } from '@/features/disease-analysis/components/confidence-ring';
import { ProcessingState } from '@/features/disease-analysis/components/processing-state';
import { RecommendationsList } from '@/features/disease-analysis/components/recommendations-list';
import { ResultActions } from '@/features/disease-analysis/components/result-actions';
import { ResultHero } from '@/features/disease-analysis/components/result-hero';
import { SeverityBadge } from '@/features/disease-analysis/components/severity-badge';
import { useReport, useReprocessReport } from '@/features/disease-analysis/hooks/use-report';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';
import { timeAgo } from '@/utils/severity';

/**
 * Soft Sage report-detail screen. Reads the report by id and renders one of
 * three states: loading, processing (the AI run is in flight), or the full
 * result. The "failed" branch from earlier versions is folded into the result
 * branch — when the engine fails we still surface whatever fields the user
 * filled out manually, plus the retry CTA in `ResultActions`.
 */
export default function ReportDetailScreen() {
  const params = useLocalSearchParams<{ id?: string }>();
  const id = params.id;

  const { data: report, isPending, isError, refetch } = useReport(id);
  const reprocess = useReprocessReport(id);

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top']} style={{ flex: 1 }}>
        <View className="flex-row items-center justify-between px-4 py-2">
          <PressableScale
            accessibilityRole="button"
            accessibilityLabel="Back"
            onPress={() => router.back()}
            haptic="selection"
            pressedScale={0.92}
            className="h-10 w-10 items-center justify-center rounded-full border border-border bg-surface"
          >
            <ChevronLeft size={20} color={palette.brand[700]} strokeWidth={2.2} />
          </PressableScale>
          <Text className="text-base font-bold text-text">Report</Text>
          <PressableScale
            accessibilityRole="button"
            accessibilityLabel="More"
            onPress={() => undefined}
            haptic="selection"
            pressedScale={0.92}
            className="h-10 w-10 items-center justify-center rounded-full border border-border bg-surface"
          >
            <MoreHorizontal size={18} color={palette.brand[700]} strokeWidth={2.2} />
          </PressableScale>
        </View>

        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ padding: 16, paddingBottom: 140, gap: 16 }}
        >
          {isPending ? (
            <View className="items-center justify-center py-20">
              <Loader size={48} />
            </View>
          ) : isError || !report ? (
            <View className="items-center gap-3 py-10">
              <Text className="text-base font-bold text-text">Couldn&apos;t load report</Text>
              <Button label="Retry" variant="ghost" onPress={() => refetch()} fullWidth={false} />
            </View>
          ) : report.processingStatus === 'PENDING' || report.processingStatus === 'PROCESSING' ? (
            <Animated.View entering={FadeIn.duration(400)}>
              <ProcessingState imageUrl={report.imageUrl} cropType={report.cropType} />
            </Animated.View>
          ) : (
            <>
              <Animated.View entering={FadeIn.duration(400)}>
                <ResultHero
                  imageUrl={report.imageUrl}
                  cropType={report.cropType}
                  severity={report.severity}
                />
              </Animated.View>

              <Animated.View entering={FadeInDown.delay(100).duration(400)}>
                <Card padding="md">
                  <View className="flex-row items-center gap-4">
                    <ConfidenceRing
                      value={report.confidence ?? 0}
                      severity={report.severity}
                      size={120}
                      strokeWidth={10}
                    />
                    <View className="flex-1 gap-1">
                      <SectionLabel>Detected</SectionLabel>
                      <Text className="text-lg font-extrabold tracking-tight text-text">
                        {report.disease ?? 'Unknown'}
                      </Text>
                      <SeverityBadge severity={report.severity} />
                      {report.processedAt ? (
                        <Text className="mt-1 text-[11px] text-text-subtle">
                          Analyzed {timeAgo(report.processedAt)}
                        </Text>
                      ) : null}
                    </View>
                  </View>
                </Card>
              </Animated.View>

              {report.notes ? (
                <Animated.View entering={FadeInDown.delay(160).duration(400)}>
                  <Card padding="md">
                    <SectionLabel>Your notes</SectionLabel>
                    <Text className="mt-1 text-sm leading-5 text-text">{report.notes}</Text>
                  </Card>
                </Animated.View>
              ) : null}

              <Animated.View entering={FadeInDown.delay(200).duration(400)} className="gap-2">
                <View className="flex-row items-center justify-between px-1">
                  <Text className="text-base font-bold tracking-tight text-text">
                    Recommended actions
                  </Text>
                  <PressableScale
                    accessibilityRole="button"
                    accessibilityLabel="Re-run analysis"
                    onPress={() => reprocess.mutate()}
                    disabled={reprocess.isPending}
                    haptic="selection"
                    pressedScale={0.95}
                  >
                    <View className="flex-row items-center gap-1">
                      <RefreshCw size={12} color={palette.brand[700]} strokeWidth={2.4} />
                      <Text className="text-xs font-bold text-brand-700">
                        {reprocess.isPending ? 'Re-analyzing…' : 'Re-run'}
                      </Text>
                    </View>
                  </PressableScale>
                </View>
                <RecommendationsList items={report.recommendations} />
              </Animated.View>

              <Animated.View entering={FadeInDown.delay(260).duration(400)}>
                <ResultActions
                  report={report}
                  onUploadAnother={() => router.replace('/upload')}
                  onViewOnMap={() => router.push('/map')}
                />
              </Animated.View>

              <Animated.View entering={FadeInDown.delay(320).duration(400)}>
                <Text className="px-2 text-[11px] text-text-subtle">
                  AI predictions are advisory. For high-severity diagnoses, consult your local
                  agricultural extension officer.
                </Text>
              </Animated.View>
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}
