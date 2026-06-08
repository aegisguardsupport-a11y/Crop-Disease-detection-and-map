import { useCallback, useReducer } from 'react';

import { offlineAiClient } from '@/features/offline-ai';
import { useCreateReport } from '@/features/upload-report/hooks/use-create-report';
import { logger } from '@/utils/logger';

import type {
  AnalysisEngine,
  AnalysisResult,
  CapturedImage,
  FlowLocation,
  FlowState,
  FlowStep,
} from './types';

type Action =
  | { type: 'SET_IMAGE'; image: CapturedImage; cropType: string | null }
  | { type: 'SET_STEP'; step: FlowStep }
  | { type: 'SET_RESULT'; result: AnalysisResult }
  | { type: 'PATCH_RESULT'; patch: Partial<AnalysisResult> }
  | { type: 'SET_LOCATION'; location: FlowLocation | null }
  | { type: 'SET_NOTES'; notes: string }
  | { type: 'SET_SHARE'; share: boolean }
  | { type: 'SET_SUBMITTED'; reportId: string }
  | { type: 'RESET' };

const initialState: FlowState = {
  step: 'capture',
  image: null,
  cropType: null,
  notes: '',
  location: null,
  result: null,
  shareToMap: true,
  submittedReportId: null,
};

function reducer(state: FlowState, action: Action): FlowState {
  switch (action.type) {
    case 'SET_IMAGE':
      return { ...state, image: action.image, cropType: action.cropType, step: 'analyzing' };
    case 'SET_STEP':
      return { ...state, step: action.step };
    case 'SET_RESULT':
      return { ...state, result: action.result, step: 'result' };
    case 'PATCH_RESULT':
      return state.result ? { ...state, result: { ...state.result, ...action.patch } } : state;
    case 'SET_LOCATION':
      return { ...state, location: action.location };
    case 'SET_NOTES':
      return { ...state, notes: action.notes };
    case 'SET_SHARE':
      return { ...state, shareToMap: action.share };
    case 'SET_SUBMITTED':
      return { ...state, step: 'submitted', submittedReportId: action.reportId };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

interface UseReportFlowOptions {
  cloudAnalyze: (image: CapturedImage, cropType: string | null) => Promise<AnalysisResult>;
}

const CLOUD_TIMEOUT_MS = 8000;

export function useReportFlow({ cloudAnalyze }: UseReportFlowOptions) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const create = useCreateReport();

  /**
   * Engine chain: cloud -> on-device -> manual. Each stage's failure is
   * logged and we move on. When all engines fail, transition to result in
   * manual mode (no badge, empty diagnosis fields).
   */
  const runAnalysis = useCallback(
    async (image: CapturedImage, cropType: string | null) => {
      const tryCloud = async (): Promise<AnalysisResult | null> => {
        try {
          const result = await Promise.race([
            cloudAnalyze(image, cropType),
            new Promise<never>((_, reject) =>
              setTimeout(() => reject(new Error('cloud-timeout')), CLOUD_TIMEOUT_MS),
            ),
          ]);
          return { ...result, engine: 'cloud' };
        } catch (err) {
          logger.warn('[report-flow] cloud analyze failed', err);
          return null;
        }
      };

      const tryOnDevice = async (): Promise<AnalysisResult | null> => {
        try {
          if (!(await offlineAiClient.isAvailable())) return null;
          const r = await offlineAiClient.analyze({
            localImageUri: image.uri,
            cropType: cropType ?? '',
          });
          if (!r.ok) return null;
          return {
            engine: 'on-device',
            disease: r.disease,
            confidence: r.confidence,
            severity: r.severity,
            recommendations: r.recommendations,
            candidates: r.candidates,
          };
        } catch (err) {
          logger.warn('[report-flow] on-device analyze failed', err);
          return null;
        }
      };

      const cloud = await tryCloud();
      if (cloud) {
        dispatch({ type: 'SET_RESULT', result: cloud });
        return;
      }
      const onDevice = await tryOnDevice();
      if (onDevice) {
        dispatch({ type: 'SET_RESULT', result: onDevice });
        return;
      }
      dispatch({
        type: 'SET_RESULT',
        result: {
          engine: 'manual',
          disease: null,
          confidence: null,
          severity: null,
          recommendations: [],
        },
      });
    },
    [cloudAnalyze],
  );

  const setImage = useCallback(
    (image: CapturedImage, cropType: string | null = null) => {
      dispatch({ type: 'SET_IMAGE', image, cropType });
      void runAnalysis(image, cropType);
    },
    [runAnalysis],
  );

  const submit = useCallback(async () => {
    if (!state.image || !state.location || !state.cropType || !state.result) return;
    const r = state.result;
    const reportId = await create.submit({
      picked: { uri: state.image.uri, width: state.image.width, height: state.image.height },
      cropTypeId: state.cropType,
      cropTypeName: state.cropType,
      notes: state.notes.trim() || undefined,
      location: state.location,
      diseaseHint: r.disease ?? undefined,
      severityHint: r.severity ?? undefined,
      shareToMap: state.shareToMap,
      // The flow has its own Submitted screen; don't auto-redirect to /reports/[id].
      skipNavigation: true,
    });
    if (reportId) dispatch({ type: 'SET_SUBMITTED', reportId });
  }, [state, create]);

  return {
    state,
    setImage,
    setStep: (step: FlowStep) => dispatch({ type: 'SET_STEP', step }),
    setLocation: (location: FlowLocation | null) => dispatch({ type: 'SET_LOCATION', location }),
    setNotes: (notes: string) => dispatch({ type: 'SET_NOTES', notes }),
    setShare: (share: boolean) => dispatch({ type: 'SET_SHARE', share }),
    patchResult: (patch: Partial<AnalysisResult>) => dispatch({ type: 'PATCH_RESULT', patch }),
    submit,
    create,
    reset: () => dispatch({ type: 'RESET' }),
  };
}

export type UseReportFlow = ReturnType<typeof useReportFlow>;

export const ENGINE_COPY: Record<AnalysisEngine, { subtitle: string; badge: string }> = {
  cloud: {
    subtitle: 'Using our high-accuracy cloud model…',
    badge: 'Cloud AI',
  },
  'on-device': {
    subtitle: 'Using on-device AI · works without internet…',
    badge: 'On-device AI',
  },
  manual: {
    subtitle: 'Fill in the details yourself.',
    badge: 'Edited by you',
  },
};
