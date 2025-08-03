import React, { useState, useEffect, useRef } from 'react';
import { Container, Typography, Button, Stack, LinearProgress, Paper, TextField } from '@mui/material';
import DiagramPromptCard from '../components/DiagramPromptCard';
import { generateLessonPack } from '../services/lessonPackService';
import { createAssignment } from '../services/assignmentService';

interface Item {
  file: File | null;
  prompt: string;
}

export default function AssignmentPage() {
  const [items, setItems] = useState<Item[]>([{ file: null, prompt: '' }]);
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState('My Assignment');
  const [logs, setLogs] = useState<string[]>([]);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  // Map backend event to user-friendly text
  function mapStatusToMessage(evt: any): string {
    const { status, idx, total } = evt;
    switch (status) {
      case 'starting':
        return `Starting lesson pack generation (total ${total})`;
      case 'processing':
        return `Understanding the image ${idx}/${total}`;
      case 'diagram_ready':
        return `Writing narration scripts ${idx}/${total}`;
      case 'scripts_ready':
        return `Converting text to braille ${idx}/${total}`;
      case 'braille_ready':
        return `Generating audio lesson ${idx}/${total}`;
      case 'audio_ready':
        return `Completed lesson pack ${idx}/${total}`;
      default:
        return status;
    }
  }

  // Auto-scroll logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const updateItem = (idx: number, data: Partial<Item>) => {
    setItems((prev) => prev.map((it, i) => (i === idx ? { ...it, ...data } : it)));
  };

  const addItem = () => setItems((prev) => [...prev, { file: null, prompt: '' }]);

  const removeItem = (idx: number) => setItems((prev) => prev.filter((_, i) => i !== idx));

  const handleGenerate = async () => {
    // validate
    if (items.some((it) => !it.file || !it.prompt.trim())) {
      alert('Please upload all images and prompts');
      return;
    }


    setLogs([]);
    setLoading(true);

    // Open SSE connection to receive live backend logs
    const es = new EventSource('http://localhost:8000/api/progress-stream');
    es.onmessage = (ev) => {
      const evt = JSON.parse(ev.data);
      if (evt.status === 'finished') {
        // ignore, we'll handle download after POST returns
        return;
      }
      const userMessage = mapStatusToMessage(evt);
      setLogs((prev) => [...prev, userMessage]);
    };
    es.onerror = () => {
      es.close();
    };

    try {
      // 1) Create assignment in DB so submissions can be linked later
      const assignmentId = await createAssignment(title, items.map((it) => ({ file: it.file as File, prompt: it.prompt })));
      console.log('Created assignment', assignmentId);

      // 2) Build lesson-pack request with assignment_id
      const formData = new FormData();
      items.forEach((it) => {
        formData.append('files', it.file as File);
      });
      formData.append('prompts', JSON.stringify(items.map((it) => it.prompt)));
      formData.append('title', title);
      formData.append('assignment_id', assignmentId.toString());

      const blob = await generateLessonPack(formData);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'lesson_pack.zip';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to generate lesson pack');
      console.error(e);
    } finally {
      es.close();
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Typography variant="h4" gutterBottom>
        Create Lesson Pack
      </Typography>
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
        <TextField
          label="Assignment Title"
          value={title}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
          fullWidth
          disabled={loading}
        />
      </Stack>
      {logs.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2, maxHeight: 200, overflow: 'auto', backgroundColor: '#f7f7f7' }}>
          {logs.map((l, i) => (
            <Typography key={i} variant="body2" component="pre" sx={{ m: 0 }}>
              {l}
            </Typography>
          ))}
          <div ref={logEndRef} />
        </Paper>
      )}
      <Stack spacing={2}>
        {items.map((it, idx) => (
          <DiagramPromptCard
            key={idx}
            idx={idx}
            file={it.file}
            prompt={it.prompt}
            onFileChange={(f) => updateItem(idx, { file: f })}
            onPromptChange={(p) => updateItem(idx, { prompt: p })}
            onDelete={() => removeItem(idx)}
          />
        ))}
        <Button variant="outlined" onClick={addItem}>Add Diagram</Button>
        <Button variant="contained" disabled={loading} onClick={handleGenerate}>
          Generate Lesson Pack
        </Button>
      </Stack>
    </Container>
  );
}
