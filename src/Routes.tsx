import React from 'react';
import { Routes, Route } from 'react-router-dom';

import AssignmentPage from './pages/Assignment';
import SubmissionsPage from './pages/Submissions';
import SubmissionDetail from './pages/SubmissionDetail';
import StudentsPage from './pages/Students';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<StudentsPage />} />
      <Route path="/students" element={<StudentsPage />} />
      <Route path="/assignment" element={<AssignmentPage />} />
      <Route path="/submissions" element={<SubmissionsPage />} />
      <Route path="/submissions/:id" element={<SubmissionDetail />} />
    </Routes>
  );
}
