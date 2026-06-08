/**
 * Image preprocessing for the CPL crop-disease classifier (MobileNetV3-Small student).
 *
 * The model expects a tensor of shape (1, 224, 224, 3), float32, with pixel
 * values in [0, 255] (NOT [0, 1] — MobileNetV3 has its own internal
 * preprocessing layer). The pipeline is:
 *   1. Resize the image to 224x224 with Expo's image manipulator (runs on the
 *      native bitmap pipeline; bilinear by default).
 *   2. Re-encode as JPEG and read it as base64.
 *   3. Decode the JPEG to raw RGBA pixels with the pure-JS jpeg-js library.
 *   4. Drop the alpha channel and copy R/G/B into a Float32Array in [0, 255].
 *
 * Pure-JS decode adds ~50–100 ms on a modern phone. If realtime camera
 * classification (>5 fps) is ever needed, switch to react-native-vision-camera
 * + vision-camera-resize-plugin to get the pixel buffer directly.
 *
 * NOTE: uses the SDK 52+ `ImageManipulator.manipulate()` context API (the same
 * one used by upload-report/utils/compress-image.ts), not the deprecated
 * `manipulateAsync` from the model hand-off template.
 */

import { Buffer } from 'buffer';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';
import jpeg from 'jpeg-js';

export const INPUT_SIZE = 224;
export const INPUT_PIXEL_COUNT = INPUT_SIZE * INPUT_SIZE * 3;

export interface Preprocessed {
  /** Float32Array of length 1 * 224 * 224 * 3 = 150_528, pixels in [0, 255]. */
  data: Float32Array;
  /** The resized JPEG URI, handy for previewing in the UI. */
  previewUri: string;
}

/**
 * Resize, decode, and convert an image at `uri` into the model's input tensor.
 *
 * @throws if the manipulator returns no base64 data or unexpected dimensions.
 */
export async function preprocessImage(uri: string): Promise<Preprocessed> {
  // 1. Resize to 224x224 RGB JPEG. compress: 1 (no extra compression) avoids
  //    artefacts that could shift the prediction.
  const context = ImageManipulator.manipulate(uri);
  context.resize({ width: INPUT_SIZE, height: INPUT_SIZE });
  const ref = await context.renderAsync();
  const resized = await ref.saveAsync({
    base64: true,
    compress: 1,
    format: SaveFormat.JPEG,
  });

  if (!resized.base64) {
    throw new Error('Image manipulator did not return base64 data');
  }

  // 2. Decode JPEG bytes -> raw RGBA pixels.
  const jpegBytes = Buffer.from(resized.base64, 'base64');
  const { data: rgbaPixels, width, height } = jpeg.decode(jpegBytes, {
    useTArray: true,
  });

  if (width !== INPUT_SIZE || height !== INPUT_SIZE) {
    throw new Error(
      `Unexpected resized image dimensions: ${width}x${height} (expected ${INPUT_SIZE}x${INPUT_SIZE})`,
    );
  }

  // 3. Convert RGBA uint8 -> RGB float32 in [0, 255].
  const out = new Float32Array(INPUT_PIXEL_COUNT);
  for (let src = 0, dst = 0; src < rgbaPixels.length; src += 4, dst += 3) {
    out[dst] = rgbaPixels[src]; // R
    out[dst + 1] = rgbaPixels[src + 1]; // G
    out[dst + 2] = rgbaPixels[src + 2]; // B
    // alpha channel ignored
  }

  return { data: out, previewUri: resized.uri };
}
