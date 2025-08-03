import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Box from '@mui/material/Box';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';

import BrailleRenderer from '../components/BrailleRenderer';
import FeedbackComposer from '../components/FeedbackComposer';
import { translateUrduToEnglish } from '../services/brailleService';
import { fetchSubmission, autogradeSubmission, AutogradeResult } from '../services/submissionService';
import { analyzeFeedback } from '../services/studentService';

const API_BASE_URL = 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Type helpers (loosely match backend shape)
// ---------------------------------------------------------------------------
interface DiagramMeta {
  image_path: string;
  prompt: string;
}
interface Answer {
  diagram_idx: number;
  answer_type: 'image' | 'audio';
  file_path: string;
  urdu_text: string;
  english_text?: string;
  braille_text?: string | null;
  errors: string[];
}
interface SubmissionData {
  id: number;
  student: string;
  answers: Answer[];
  assignment: {
    id: number;
    title: string;
    diagrams: DiagramMeta[];
  };
}

export default function SubmissionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [tab, setTab] = useState(0);
  const [data, setData] = useState<SubmissionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [translating, setTranslating] = useState(false);
  const [aiGrade, setAiGrade] = useState<AutogradeResult | null>(null);
  const [grading, setGrading] = useState(false);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [customFeedback, setCustomFeedback] = useState('');

  // -------------------------------------------------------------------------
  // Load submission details
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchSubmission(Number(id))
      .then((d) => {
        setData(d as unknown as SubmissionData);
      })
      .catch((e) => {
        console.error(e);
        setError('Failed to load submission');
      })
      .finally(() => setLoading(false));
  }, [id]);

  // -------------------------------------------------------------------------
  // Fallback translation if english_text missing
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!data) return;
    const answer = data.answers[0];
    if (answer.english_text || !answer.urdu_text) return; // already translated or no urdu text

    setTranslating(true);
    translateUrduToEnglish(answer.urdu_text)
      .then((eng) => {
        setData((prev) => {
          if (!prev) return prev;
          const updated = { ...prev };
          updated.answers[0].english_text = eng;
          return updated;
        });
      })
      .catch((e) => console.error('Translation failed', e))
      .finally(() => setTranslating(false));
  }, [data]);

  // -------------------------------------------------------------------------
  // Rendering helpers
  // -------------------------------------------------------------------------
  if (loading) {
    return (
      <Container sx={{ textAlign: 'center', mt: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !data) {
    return (
      <Container>
        <Alert severity="error">{error || 'Submission not found'}</Alert>
      </Container>
    );
  }

  const answer = data.answers[0];
  const diagram = data.assignment.diagrams[answer.diagram_idx];

  const downloadFeedback = async (feedback: string) => {
    // Analyze feedback and update student profile
    if (aiGrade) {
      try {
        await analyzeFeedback(feedback, aiGrade.correct, data.student);
        console.log('Student profile updated with feedback analysis');
      } catch (e) {
        console.error('Failed to analyze feedback:', e);
      }
    }

    // Create feedback text file
    const content = `Submission #${id} - ${data.student}\n\nFeedback: ${feedback}\n\nBraille Text:\n${answer.braille_text || 'N/A'}\n\nUrdu Text:\n${answer.urdu_text}\n\nEnglish Text:\n${answer.english_text}`;
    const textBlob = new Blob([content], { type: 'text/plain' });
    const textUrl = URL.createObjectURL(textBlob);
    const textLink = document.createElement('a');
    textLink.href = textUrl;
    textLink.download = `feedback_submission_${id}.txt`;
    textLink.click();
    URL.revokeObjectURL(textUrl);

    // If there's braille text and error positions, generate SVG
    if (answer.braille_text && aiGrade && !aiGrade.correct && aiGrade.error_start !== undefined && aiGrade.error_end !== undefined) {
      const brailleText = answer.braille_text.replace(/\n/g, ' ');
      const beforeError = brailleText.slice(0, aiGrade.error_start);
      const errorText = brailleText.slice(aiGrade.error_start, aiGrade.error_end);
      const afterError = brailleText.slice(aiGrade.error_end);

      // Create SVG with red squiggly underline for error
      const svgContent = `
        <svg xmlns="http://www.w3.org/2000/svg" width="800" height="200">
          <defs>
            <path id="squiggly" d="M0,0 Q2,2 4,0 Q6,2 8,0 Q10,2 12,0" stroke="red" stroke-width="2" fill="none"/>
          </defs>
          <style>
            .braille-text { font-family: SimBraille, sans-serif; font-size: 32px; fill: black; }
          </style>
          <text x="10" y="50" class="braille-text">
            <tspan>${beforeError}</tspan><tspan>${errorText}</tspan><tspan>${afterError}</tspan>
          </text>
          <g transform="translate(${10 + beforeError.length * 16}, 55)">
            <use href="#squiggly" transform="scale(${errorText.length * 1.3}, 1)"/>
          </g>
        </svg>
      `;

      const svgBlob = new Blob([svgContent], { type: 'image/svg+xml' });
      const svgUrl = URL.createObjectURL(svgBlob);
      const svgLink = document.createElement('a');
      svgLink.href = svgUrl;
      svgLink.download = `braille_submission_${id}.svg`;
      svgLink.click();
      URL.revokeObjectURL(svgUrl);
    }
  };

  const highlightedUrdu = (answer.urdu_text || '')
    .replace(/\n/g, ' ')
    .split(' ')
    .map((word, idx) => {
      const isError = answer.errors?.includes(word) || false;
      return (
        <span key={idx} style={{ textDecoration: isError ? 'underline wavy red' : 'none' }}>
          {word + ' '}
        </span>
      );
    });

  // Helper function to fix file paths for static serving
  const getFileUrl = (filePath: string) => {
    // Remove 'backend/' prefix if present since static files are served from /uploads
    const cleanPath = filePath.replace(/^backend\//, '');
    return `${API_BASE_URL}/${cleanPath}`;
  };

  const submissionMedia = answer.answer_type === 'image' ? (
    <img
      src={getFileUrl(answer.file_path)}
      alt="Student submission"
      style={{ maxWidth: '100%', borderRadius: 8 }}
    />
  ) : (
    <audio controls src={getFileUrl(answer.file_path)} style={{ width: '100%' }} />
  );

  return (
    <Container maxWidth="md">
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)}>
        Back
      </Button>
      <Typography variant="h4" gutterBottom>
        Submission #{id} – {data.student}
      </Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Answer" />
        <Tab label="Feedback" />
      </Tabs>

      {tab === 0 && (
        <Stack spacing={3}>
          {/* Original diagram & question */}
          <div>
            <Typography variant="h6" gutterBottom>
              Original Question & Image
            </Typography>
            <img
              src={getFileUrl(diagram.image_path)}
              alt="Original question"
              style={{ maxWidth: '100%', borderRadius: 8 }}
            />
            <Typography sx={{ mt: 1 }}>{diagram.prompt}</Typography>
          </div>

          {/* Student submission media */}
          <div>
            <Typography variant="h6" gutterBottom>
              Student Submission ({answer.answer_type})
            </Typography>
            {submissionMedia}
          </div>

          {/* Translations */}
          <div>
            <Typography variant="h6" gutterBottom>
              Translated Text
            </Typography>
            <Typography variant="subtitle1" fontWeight="bold">
              English
            </Typography>
            {translating && (
              <Box display="inline-block" ml={1}>
                <CircularProgress size={16} />
              </Box>
            )}
            <Typography sx={{ mb: 2 }}>{answer.english_text ?? '—'}</Typography>

            <Typography variant="subtitle1" fontWeight="bold">
              Urdu
            </Typography>
            <Typography>{highlightedUrdu}</Typography>
          </div>

          {/* AI Grading */}
          <div>
            <Typography variant="h6" gutterBottom>
              AI Grading
            </Typography>
{aiGrade ? (
              <div>
                <Typography>{aiGrade.explanation}</Typography>
                <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                  <Button variant="contained" color="success" onClick={() => downloadFeedback(aiGrade.explanation)}>
                    Accept
                  </Button>
                  <Button variant="contained" color="error" onClick={() => setShowFeedbackForm(true)}>
                    Reject
                  </Button>
                </Stack>
                {showFeedbackForm && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="h6">Provide Custom Feedback:</Typography>
                    <textarea
                      value={customFeedback}
                      onChange={(e) => setCustomFeedback(e.target.value)}
                      style={{ width: '100%', minHeight: '100px', marginTop: '8px' }}
                      placeholder="Enter your feedback here..."
                    />
                    <Button 
                      variant="contained" 
                      sx={{ mt: 1 }}
                      onClick={() => downloadFeedback(customFeedback)}
                    >
                      Download
                    </Button>
                  </Box>
                )}
              </div>
            ) : (
              <Button variant="outlined" disabled={grading} onClick={async () => {
                setGrading(true);
                try {
                  const grade = await autogradeSubmission(Number(id));
                  setAiGrade(grade);
                } catch (e) {
                  console.error(e);
                  alert('Autograde failed');
                } finally {
                  setGrading(false);
                }
              }}>
                {grading ? 'Grading…' : 'Autograde'}
              </Button>
            )}
          </div>

          {/* Braille rendering if available */}
          {answer.braille_text && (
            <div>
              <Typography variant="h6" gutterBottom>
                Braille Rendering
              </Typography>
              <BrailleRenderer 
                text={answer.braille_text.replace(/\n/g, ' ')} 
                alreadyBraille={true}
                errorStart={aiGrade?.error_start}
                errorEnd={aiGrade?.error_end}
              />
            </div>
          )}
        </Stack>
      )}

      {tab === 1 && (
        <FeedbackComposer
          onSave={(text, url) => {
            console.log('Feedback saved', { text, url });
          }}
        />
      )}
    </Container>
  );
}
