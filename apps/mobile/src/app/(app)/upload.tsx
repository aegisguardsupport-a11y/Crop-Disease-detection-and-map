import { router } from 'expo-router';
import { useEffect, useRef } from 'react';

import { analyzeImage } from '@/features/disease-analysis/api';
import {
  AnalyzingScreen,
  EditDetailsSheet,
  ResultScreen,
  SubmittedScreen,
} from '@/features/report-flow';
import { CaptureScreen } from '@/features/report-flow/screens/capture-lazy';
import type { EditDetailsSheetHandle } from '@/features/report-flow/components/edit-details-sheet';
import { useReportFlow } from '@/features/report-flow/use-report-flow';
import { useCurrentLocation } from '@/features/upload-report/hooks';
import { View } from '@/tw';

/**
 * Tab entry for the new report flow. Drives a four-step state machine:
 * Capture → Analyzing → Result → Submitted, falling through cloud → on-device
 * → manual when an engine is unavailable.
 */
export default function UploadScreen() {
  const flow = useReportFlow({
    cloudAnalyze: (image, cropType) =>
      analyzeImage({ imageUrl: image.uri, cropType: cropType ?? undefined }),
  });

  const editSheetRef = useRef<EditDetailsSheetHandle>(null);

  const locationCtl = useCurrentLocation(true);
  useEffect(() => {
    if (locationCtl.location) {
      flow.setLocation({
        latitude: locationCtl.location.latitude,
        longitude: locationCtl.location.longitude,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- flow.setLocation is stable
  }, [locationCtl.location]);

  const submitting =
    flow.create.state === 'uploading' || flow.create.state === 'compressing';

  let body: React.ReactNode = null;
  switch (flow.state.step) {
    case 'capture':
      body = <CaptureScreen onCaptured={flow.setImage} onCancel={flow.reset} />;
      break;
    case 'analyzing':
      body = flow.state.image ? <AnalyzingScreen image={flow.state.image} /> : <View />;
      break;
    case 'result':
      body =
        flow.state.image && flow.state.result ? (
          <ResultScreen
            image={flow.state.image}
            result={flow.state.result}
            shareToMap={flow.state.shareToMap}
            submitting={submitting}
            onShareChange={flow.setShare}
            onEdit={() => editSheetRef.current?.present()}
            onPickCandidate={(disease) =>
              flow.patchResult({ disease, candidates: undefined, confidence: 1 })
            }
            onConfirm={() => void flow.submit()}
          />
        ) : (
          <View />
        );
      break;
    case 'submitted':
      body = flow.state.result ? (
        <SubmittedScreen
          result={flow.state.result}
          cropType={flow.state.cropType}
          shareToMap={flow.state.shareToMap}
          reportId={flow.state.submittedReportId}
          onAnother={() => {
            flow.reset();
            router.replace('/upload');
          }}
        />
      ) : (
        <View />
      );
      break;
  }

  return (
    <>
      {body}
      {flow.state.result ? (
        <EditDetailsSheet
          ref={editSheetRef}
          initial={flow.state.result}
          onSave={flow.patchResult}
        />
      ) : null}
    </>
  );
}
