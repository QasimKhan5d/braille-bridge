const API_BASE_URL = 'http://localhost:8000';

export interface SubmitAnswerArgs {
  assignmentId: number;
  student: string;
  answerType: 'image' | 'audio';
  file: File;
}

export async function submitAnswer(args: SubmitAnswerArgs): Promise<number> {
  const formData = new FormData();
  formData.append('student', args.student);
  formData.append('answer_type', args.answerType);
  formData.append('file', args.file);

  const res = await fetch(`${API_BASE_URL}/api/assignments/${args.assignmentId}/submit`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  const data = await res.json();
  return data.submission_id as number;
}

export interface Submission {
  id: number;
  assignment_id: number;
  student: string;
  answers: any[];
}

export async function fetchSubmissions(): Promise<Submission[]> {
  const res = await fetch(`${API_BASE_URL}/api/submissions`);
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export async function fetchSubmission(id: number): Promise<Submission> {
  const res = await fetch(`${API_BASE_URL}/api/submissions/${id}`);
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export interface AutogradeResult {
  correct: boolean;
  explanation: string;
  error_start?: number;
  error_end?: number;
}

export async function autogradeSubmission(id: number): Promise<AutogradeResult> {
  const res = await fetch(`${API_BASE_URL}/api/submissions/${id}/autograde`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}
