import config from '../config';

export async function generateLessonPack(formData: FormData): Promise<Blob> {
  const res = await fetch(`${config.API_BASE_URL}/api/lesson-pack`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.blob();
}