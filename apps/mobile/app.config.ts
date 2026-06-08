import type { ConfigContext, ExpoConfig } from 'expo/config';

/**
 * Single source of truth for Expo config.
 *
 * Secrets (e.g. GOOGLE_MAPS_API_KEY) come from env so we never commit them:
 *   - Local dev:   apps/mobile/.env (gitignored)
 *   - EAS Build:   eas secret:create --scope project --name GOOGLE_MAPS_API_KEY --value <key>
 *
 * The key still ends up inside the APK (Google requires it in AndroidManifest).
 * Real protection comes from restricting the key to the app's package name +
 * SHA-1 fingerprint in Google Cloud Console — do that before any public release.
 */
export default ({ config: _ }: ConfigContext): ExpoConfig => {
  const googleMapsApiKey = process.env.GOOGLE_MAPS_API_KEY;

  if (!googleMapsApiKey) {
    // eslint-disable-next-line no-console
    console.warn(
      '[app.config] GOOGLE_MAPS_API_KEY is not set — Android maps will fail at runtime.',
    );
  }

  return {
    name: 'AgroRadar',
    slug: 'agroradar',
    version: '1.0.0',
    orientation: 'portrait',
    icon: './assets/images/icon.png',
    scheme: 'agroradar',
    userInterfaceStyle: 'automatic',
    ios: {
      icon: './assets/expo.icon',
      supportsTablet: true,
      bundleIdentifier: 'com.agroradar.app',
    },
    android: {
      package: 'com.agroradar.app',
      predictiveBackGestureEnabled: false,
      adaptiveIcon: {
        backgroundColor: '#10b981',
        foregroundImage: './assets/images/android-icon-foreground.png',
        backgroundImage: './assets/images/android-icon-background.png',
        monochromeImage: './assets/images/android-icon-monochrome.png',
      },
      config: {
        googleMaps: {
          apiKey: googleMapsApiKey ?? '',
        },
      },
    },
    web: {
      output: 'static',
      favicon: './assets/images/favicon.png',
    },
    // Bundle the offline TFLite model + label map into the binary so on-device
    // inference works with zero network calls.
    assetBundlePatterns: ['assets/**/*'],
    plugins: [
      'expo-router',
      [
        'expo-splash-screen',
        {
          backgroundColor: '#047857',
          android: {
            image: './assets/images/splash-icon.png',
            imageWidth: 96,
          },
        },
      ],
      [
        'expo-notifications',
        {
          color: '#10b981',
          defaultChannel: 'default',
        },
      ],
      [
        'expo-camera',
        {
          cameraPermission:
            'AgroRadar uses your camera to photograph crops for disease analysis.',
          recordAudioAndroid: false,
          barcodeScannerEnabled: false,
        },
      ],
      [
        'react-native-fast-tflite',
        {
          enableCoreMLDelegate: true,
          enableAndroidGpuLibraries: true,
        },
      ],
    ],
    experiments: {
      typedRoutes: true,
      reactCompiler: true,
    },
    extra: {
      eas: {
        projectId: 'd90cc6a1-438a-4f0d-8aa7-9fdc91ca0d33',
      },
    },
    owner: 'pranavloveher',
  };
};
