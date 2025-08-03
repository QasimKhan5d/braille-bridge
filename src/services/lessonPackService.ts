export async function generateLessonPack(formData: FormData): Promise<Blob> {
  const res = await fetch('http://localhost:8000/api/lesson-pack', {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.blob();
}