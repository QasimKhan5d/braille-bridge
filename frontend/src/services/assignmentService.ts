import config from '../config';

const API_BASE_URL = config.API_BASE_URL;

export interface DiagramInput {
  file: File;
  prompt: string;
}

export async function createAssignment(title: string, diagrams: DiagramInput[]): Promise<number> {
  const formData = new FormData();
  diagrams.forEach((d) => {
    formData.append('files', d.file);
  });
  formData.append('prompts', JSON.stringify(diagrams.map((d) => d.prompt)));
  formData.append('title', title);

  const res = await fetch(`${API_BASE_URL}/api/assignments`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  const data = await res.json();
  return data.assignment_id as number;
}

export interface Assignment {
  id: number;
  title: string;
  diagrams: { image_path: string; prompt: string }[];
}

export async function fetchAssignments(): Promise<Assignment[]> {
  const res = await fetch(`${API_BASE_URL}/api/assignments`);
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export async function fetchAssignment(id: number): Promise<Assignment> {
  const res = await fetch(`${API_BASE_URL}/api/assignments/${id}`);
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}
