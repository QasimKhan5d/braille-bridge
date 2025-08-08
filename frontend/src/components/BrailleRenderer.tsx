import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { toBraille } from '../utils/braille';

interface BrailleRendererProps {
  text: string;
  alreadyBraille?: boolean;
  errorStart?: number;
  errorEnd?: number;
}

function isBraillePattern(str: string): boolean {
  // detect if string already contains braille unicode patterns
  if (!str) return false;
  let brailleCount = 0;
  for (const ch of str) {
    const code = ch.charCodeAt(0);
    if (code >= 0x2800 && code <= 0x28FF) brailleCount += 1;
  }
  return brailleCount / str.length > 0.5;
}

export default function BrailleRenderer({ text, alreadyBraille, errorStart, errorEnd }: BrailleRendererProps) {
  const displayText = alreadyBraille || isBraillePattern(text) ? text : toBraille(text);
  
  if (errorStart !== undefined && errorEnd !== undefined) {
    const beforeError = displayText.slice(0, errorStart);
    const errorText = displayText.slice(errorStart, errorEnd);
    const afterError = displayText.slice(errorEnd);
    
    return (
      <Box sx={{ p: 1, border: '1px dashed', borderRadius: 1, mb: 4 }}>
        <Typography
          component="span"
          sx={{ fontSize: 32, lineHeight: 1.6, fontFamily: 'SimBraille, sans-serif', whiteSpace: 'normal', wordBreak: 'break-word' }}
        >
          {beforeError}
          <span style={{ textDecoration: 'underline wavy red' }}>
            {errorText}
          </span>
          {afterError}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 1, border: '1px dashed', borderRadius: 1, mb: 4 }}>
      <Typography
        component="span"
        sx={{ fontSize: 32, lineHeight: 1.6, fontFamily: 'SimBraille, sans-serif', whiteSpace: 'normal', wordBreak: 'break-word' }}
      >
        {displayText}
      </Typography>
    </Box>
  );
}