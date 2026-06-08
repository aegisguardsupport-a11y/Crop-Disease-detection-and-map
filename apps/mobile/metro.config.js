// metro.config.js
const { getDefaultConfig } = require('expo/metro-config');
const { withNativewind } = require('nativewind/metro');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Bundle the offline TFLite model as a static asset so `require('...tflite')`
// resolves to an on-device file path that react-native-fast-tflite can open.
config.resolver.assetExts.push('tflite');

module.exports = withNativewind(config, {
  inlineVariables: false,
  globalClassNamePolyfill: false,
});
