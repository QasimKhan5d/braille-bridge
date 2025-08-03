import React, { useEffect, useState } from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useNavigate } from 'react-router-dom';

import { fetchAssignments, Assignment } from '../services/assignmentService';
import { fetchSubmissions, Submission } from '../services/submissionService';

export default function SubmissionsPage() {
  const navigate = useNavigate();

  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [selected, setSelected] = useState<Assignment | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);

  // Load assignments once
  useEffect(() => {
    fetchAssignments()
      .then(setAssignments)
      .catch((err) => console.error('Failed to fetch assignments', err));
  }, []);

  // ---------------------------------------------------------------------------
  // Table column definitions
  // ---------------------------------------------------------------------------
  const assignmentColumns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 80 },
    { field: 'title', headerName: 'Title', flex: 1 },
    { field: 'numQuestions', headerName: '# Questions', width: 120 },
  ];

  const submissionColumns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'student', headerName: 'Student', width: 140 },
    {
      field: 'type',
      headerName: 'Type',
      width: 100,
      valueGetter: (params) => params?.row?.answers?.[0]?.answer_type ?? '',
    },
  ];

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------
  const handleAssignmentClick = (params: any) => {
    const assignment = assignments.find((a) => a.id === params.id);
    if (!assignment) return;
    setSelected(assignment);

    fetchSubmissions()
      .then((all) => {
        const filtered = all.filter((s) => s.assignment_id === assignment.id);
        setSubmissions(filtered);
      })
      .catch((err) => console.error('Failed to fetch submissions', err));
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  if (!selected) {
    return (
      <Container maxWidth="lg" sx={{ height: '80vh' }}>
        <Typography variant="h4" gutterBottom>
          Assignments
        </Typography>
        <DataGrid
          rows={assignments.map(assignment => ({
            ...assignment,
            numQuestions: assignment.diagrams?.length ?? 0
          }))}
          columns={assignmentColumns}
          pageSizeOptions={[5]}
          onRowClick={handleAssignmentClick}
          loading={assignments.length === 0}
        />
      </Container>
    );
  }

  const gridRows = submissions.map((s) => ({
    id: s.id,
    student: s.student,
    answers: s.answers,
  }));

  return (
    <Container maxWidth="lg" sx={{ height: '80vh' }}>
      <Button sx={{ mb: 2 }} onClick={() => { setSelected(null); setSubmissions([]); }}>
        ← Back to assignments
      </Button>
      <Typography variant="h4" gutterBottom>
        Submissions for: {selected.title}
      </Typography>
      <DataGrid
        rows={gridRows}
        columns={submissionColumns}
        pageSizeOptions={[5]}
        onRowClick={(params) => navigate(`/submissions/${params.id}`)}
      />
    </Container>
  );
}
