import React, { useState } from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import DownloadIcon from '@mui/icons-material/Download';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';

import BrailleRenderer from '../components/BrailleRenderer';
import { toBraille } from '../utils/braille';
import useGemmaTTS from '../hooks/useGemmaTTS';

export default function FeedbackPage() {
  const [feedback, setFeedback] = useState('');
  const { generateAudio, loading, audioUrl } = useGemmaTTS();

  const handleExportSvg = () => {
    const brailleText = toBraille(feedback);
    const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" width="500" height="100">
      <text x="10" y="50" font-family="SimBraille, sans-serif" font-size="32">${brailleText}</text>
    </svg>`;
    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'feedback.svg';
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleGenerateAudio = () => {
    if (!feedback.trim()) return;
    generateAudio(feedback);
  };

  return (
    <Container maxWidth="md">
      <Typography variant="h4" gutterBottom>
        Feedback Composer
      </Typography>
      <Stack spacing={3}>
        <TextField
          label="Write feedback (Urdu or English)"
          multiline
          rows={4}
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          fullWidth
        />

        {feedback && (
          <div>
            <Typography variant="h6" gutterBottom>
              Braille Preview
            </Typography>
            <BrailleRenderer text={feedback} />
          </div>
        )}

        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            disabled={!feedback.trim()}
            onClick={handleExportSvg}
          >
            Export as SVG
          </Button>
          <Button
            variant="outlined"
            startIcon={loading ? <CircularProgress size={20} /> : <RecordVoiceOverIcon />}
            disabled={!feedback.trim() || loading}
            onClick={handleGenerateAudio}
          >
            {loading ? 'Generating…' : 'Generate Audio (Stub)'}
          </Button>
        </Stack>

        {audioUrl && (
          <Alert severity="success">Audio generated for feedback (stub).</Alert>
        )}
        {audioUrl && <audio controls src={audioUrl} style={{ width: '100%' }} />}
      </Stack>
    </Container>
  );
}
