import config from '../config';

const API_BASE_URL = config.API_BASE_URL;

export interface BrailleProcessingResult {
  braille_text: string;
  urdu_text: string;
  braille_lines: string[];
  urdu_lines: string[];
  errors: string[];
}

export async function processBrailleImage(file: File): Promise<BrailleProcessingResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/process-braille`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to process image: ${errorText}`);
  }

  return response.json();
}

export async function translateTextToBraille(text: string, lang: 'urdu' | 'english'): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/text-to-braille`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, lang }),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  const data = await response.json();
  return data.braille_text as string;
}

export async function translateUrduToEnglish(text: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/translate-urdu-english`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  const data = await response.json();
  return data.english_text as string;
}

export async function checkHealth(): Promise<{ status: string; model_loaded: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error('Backend health check failed');
  }
  return response.json();
} 