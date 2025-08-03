import React from 'react';
import { useDropzone } from 'react-dropzone';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';

interface DropzoneProps {
  onFileAccepted: (file: File) => void;
}

export default function Dropzone({ onFileAccepted }: DropzoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'image/*': [] },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles && acceptedFiles.length > 0) {
        onFileAccepted(acceptedFiles[0]);
      }
    },
  });

  return (
    <Paper
      variant="outlined"
      {...getRootProps()}
      sx={{
        p: 2,
        textAlign: 'center',
        cursor: 'pointer',
        backgroundColor: isDragActive ? 'action.hover' : 'inherit',
      }}
    >
      <input {...getInputProps()} />
      <Typography>
        {isDragActive ? 'Drop the diagram here...' : 'Drag & drop a diagram image, or click to select'}
      </Typography>
    </Paper>
  );
}
