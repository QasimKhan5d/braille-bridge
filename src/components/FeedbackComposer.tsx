import React, { useState, useEffect } from 'react';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';

import DownloadIcon from '@mui/icons-material/Download';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormLabel from '@mui/material/FormLabel';
import { translateTextToBraille } from '../services/brailleService';

import BrailleRenderer from './BrailleRenderer';
import { toBraille } from '../utils/braille';


interface FeedbackComposerProps {
  onExport?: (svgBlob: Blob) => void;
  onSave?: (text: string, audioUrl?: string) => void;
}

export default function FeedbackComposer({ onExport, onSave }: FeedbackComposerProps) {
  const [feedback, setFeedback] = useState('');
  const [lang, setLang] = useState<'urdu' | 'english'>('urdu');
  const [braillePreview, setBraillePreview] = useState<string>('');

  useEffect(() => {
    const fetchBraille = async () => {
      if (!feedback.trim()) {
        setBraillePreview('');
        return;
      }
      try {
        const br = await translateTextToBraille(feedback, lang);
        setBraillePreview(br);
      } catch (e) {
        console.error(e);
        setBraillePreview('');
      }
    };
    fetchBraille();
  }, [feedback, lang]);

  const handleExportSvg = () => {
    const brailleText = braillePreview || toBraille(feedback);
    const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" width="500" height="100">
      <text x="10" y="50" font-family="SimBraille, sans-serif" font-size="32">${brailleText}</text>
    </svg>`;
    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    if (onExport) onExport(blob);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'feedback.svg';
    link.click();
    URL.revokeObjectURL(url);
  };



  return (
    <Stack spacing={3}>
      <TextField
        label="Write feedback (Urdu or English)"
        multiline
        rows={4}
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        fullWidth
      />

      {/* language selector */}
        <div>
          <FormLabel component="legend">Input Language</FormLabel>
          <RadioGroup row value={lang} onChange={(e) => setLang(e.target.value as 'urdu' | 'english')}>
            <FormControlLabel value="urdu" control={<Radio />} label="Urdu" />
            <FormControlLabel value="english" control={<Radio />} label="English" />
          </RadioGroup>
        </div>

        {feedback && (
        <div>
          <Typography variant="h6" gutterBottom>
            Braille Preview
          </Typography>
          <BrailleRenderer text={braillePreview} alreadyBraille />
        </div>
      )}

      <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          disabled={!feedback.trim()}
          onClick={handleExportSvg}
        >
          Export SVG
        </Button>
    </Stack>
  );
}
