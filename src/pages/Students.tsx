import React, { useState, useEffect } from 'react';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import Avatar from '@mui/material/Avatar';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Stack from '@mui/material/Stack';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import SchoolIcon from '@mui/icons-material/School';
import HearingIcon from '@mui/icons-material/Hearing';
import TouchAppIcon from '@mui/icons-material/TouchApp';
import { fetchStudents, StudentProfile } from '../services/studentService';

export default function StudentsPage() {
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [selected, setSelected] = useState<StudentProfile | null>(null);

  useEffect(() => {
    fetchStudents()
      .then((data) => {
        setStudents(data);
        if (data.length > 0) setSelected(data[0]);
      })
      .catch((err) => console.error('Failed to fetch students:', err));
  }, []);

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Students Insights
      </Typography>
      <Grid container spacing={3}>
        {/* Students list */}
        <Grid item xs={12} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Students
              </Typography>
              <List>
                {students.map((s) => (
                  <ListItem key={s.id} disablePadding>
                    <ListItemButton
                      selected={selected?.id === s.id}
                      onClick={() => setSelected(s)}
                    >
                      <ListItemAvatar>
                        <Avatar>
                          <SchoolIcon />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={s.name}
                        secondary={`ID: ${s.id}`}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Detail */}
        <Grid item xs={12} md={8}>
          {selected ? (
            <Card variant="outlined">
              <CardContent>
                <Stack spacing={2}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Avatar>
                      <SchoolIcon />
                    </Avatar>
                    <Typography variant="h5">{selected.name}</Typography>
                  </Box>

                  <div>
                    <Typography variant="subtitle1">Strengths</Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
                      {selected.strengths?.length > 0 ? (
                        selected.strengths.map((strength, idx) => (
                          <Chip key={idx} label={strength} color="success" />
                        ))
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No strengths recorded yet
                        </Typography>
                      )}
                    </Stack>
                  </div>

                  <div>
                    <Typography variant="subtitle1">Top Challenges</Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap">
                      {selected.challenges?.length > 0 ? (
                        selected.challenges.map((challenge, idx) => (
                          <Chip key={idx} label={challenge} color="warning" />
                        ))
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No challenges recorded yet
                        </Typography>
                      )}
                    </Stack>
                  </div>
                </Stack>
              </CardContent>
            </Card>
          ) : (
            <Typography>Select a student to view insights</Typography>
          )}
        </Grid>
      </Grid>
    </Container>
  );
}
