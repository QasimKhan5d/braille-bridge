import config from '../config';

const API_BASE_URL = config.API_BASE_URL;

export async function analyzeFeedback(feedback: string, isCorrect: boolean, studentName: string): Promise<{ trait: string; type: string }> {
  const res = await fetch(`${API_BASE_URL}/api/feedback/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      feedback,
      is_correct: isCorrect,
      student_name: studentName
    }),
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export interface StudentProfile {
  id: number;
  name: string;
  strengths: string[];
  challenges: string[];
}

export async function fetchStudents(): Promise<StudentProfile[]> {
  const res = await fetch(`${API_BASE_URL}/api/students`);
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}