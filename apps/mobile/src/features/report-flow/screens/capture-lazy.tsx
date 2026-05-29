import { lazy, Suspense } from 'react';
import { ActivityIndicator } from 'react-native';
import { ErrorBoundary } from 'react-error-boundary';

import { palette } from '@/theme/colors';
import { logger } from '@/utils/logger';
import { View } from '@/tw';

import type { CapturedImage } from '../types';

import { CaptureFallbackScreen } from './capture-fallback';

interface Props {
  onCaptured: (image: CapturedImage) => void;
  onCancel: () => void;
}

/**
 * Lazily-loaded in-page camera. `expo-camera`'s native module loads eagerly at
 * import time, so we defer importing the real `CaptureScreen` until this
 * component renders (i.e. when the user actually opens the report flow), and
 * wrap it in an error boundary. If the native module is missing — most often
 * because the dev client was built before `expo-camera` was installed — we
 * drop to a camera-free fallback that uses `expo-image-picker` instead.
 */
const LazyCaptureScreen = lazy(() =>
  import('./capture-screen').then((m) => ({ default: m.CaptureScreen })),
);

function CaptureLoading() {
  return (
    <View className="flex-1 items-center justify-center bg-bg">
      <ActivityIndicator color={palette.brand[600]} />
    </View>
  );
}

export function CaptureScreen({ onCaptured, onCancel }: Props) {
  return (
    <ErrorBoundary
      onError={(error) => logger.warn('[report-flow] camera unavailable, using fallback', error)}
      fallbackRender={() => (
        <CaptureFallbackScreen onCaptured={onCaptured} onCancel={onCancel} />
      )}
    >
      <Suspense fallback={<CaptureLoading />}>
        <LazyCaptureScreen onCaptured={onCaptured} onCancel={onCancel} />
      </Suspense>
    </ErrorBoundary>
  );
}
