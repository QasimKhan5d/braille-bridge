export interface Student {
  id: number;
  name: string;
  modality: 'audio' | 'braille';
  needs: string[];
  lastHomework: string;
}

export const students: Student[] = [
  {
    id: 1,
    name: 'Ali',
    modality: 'audio',
    needs: ['Listening comprehension gap', 'Vocabulary – "پانی" usage'],
    lastHomework: '2024-05-04',
  },
  {
    id: 2,
    name: 'Fatima',
    modality: 'braille',
    needs: ['Misspells "پانی"', 'Capitalisation errors'],
    lastHomework: '2024-05-03',
  },
];
