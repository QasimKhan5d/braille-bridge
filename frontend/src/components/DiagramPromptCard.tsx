import React from 'react';
import { Card, CardContent, IconButton, TextField, Button, Stack, Typography } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

interface Props {
  idx: number;
  file: File | null;
  prompt: string;
  onFileChange: (file: File | null) => void;
  onPromptChange: (text: string) => void;
  onDelete: () => void;
}

export default function DiagramPromptCard({ idx, file, prompt, onFileChange, onPromptChange, onDelete }: Props) {
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Question {idx + 1}</Typography>
            {idx > 0 && (
              <IconButton onClick={onDelete} aria-label="delete">
                <DeleteIcon />
              </IconButton>
            )}
          </Stack>
          {file ? (
            <img src={URL.createObjectURL(file)} alt={`question-${idx}`} style={{ maxWidth: '100%', maxHeight: 200 }} />
          ) : (
            <Button variant="contained" onClick={handleSelect}>Upload Image</Button>
          )}
          <input
            type="file"
            accept="image/*"
            hidden
            ref={fileInputRef}
            onChange={(e) => {
              const f = e.target.files?.[0] || null;
              onFileChange(f);
            }}
          />
          <TextField
            label="Question prompt"
            multiline
            rows={3}
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            fullWidth
          />
        </Stack>
      </CardContent>
    </Card>
  );
}
