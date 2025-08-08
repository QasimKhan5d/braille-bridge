import { useState } from 'react';

/**
 * Stub for Gemma TTS.
 * Simulates an API call that returns a URL to an audio file generated from the provided text.
 */
export default function useGemmaTTS() {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const generateAudio = async (text: string) => {
    setLoading(true);
    // Simulate latency
    await new Promise((resolve) => setTimeout(resolve, 1200));
    // For stub purposes we just return a short silent WAV data URI so <audio> can play something.
    // 1-second silence wav (44.1 kHz, 16-bit PCM, mono)
    const silentWavBase64 =
      'UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=';
    const url = `data:audio/wav;base64,${silentWavBase64}`;
    setAudioUrl(url);
    setLoading(false);
    return url;
  };
  return { generateAudio, audioUrl, loading };
}
