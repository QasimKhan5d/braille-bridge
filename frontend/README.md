# Braille Bridge Frontend

React TypeScript frontend for the Braille Bridge application, providing an intuitive interface for braille education and learning.

## Project Structure

```
frontend/
├── src/                    # Source code
│   ├── components/        # Reusable UI components
│   │   ├── BrailleRenderer.tsx
│   │   ├── DiagramPromptCard.tsx
│   │   ├── Dropzone.tsx
│   │   └── FeedbackComposer.tsx
│   ├── pages/            # Page components
│   │   ├── Assignment.tsx
│   │   ├── Feedback.tsx
│   │   ├── Students.tsx
│   │   ├── SubmissionDetail.tsx
│   │   └── Submissions.tsx
│   ├── services/         # API service functions
│   │   ├── assignmentService.ts
│   │   ├── brailleService.ts
│   │   ├── lessonPackService.ts
│   │   ├── studentService.ts
│   │   └── submissionService.ts
│   ├── hooks/           # Custom React hooks
│   │   └── useGemmaTTS.ts
│   ├── utils/           # Utility functions
│   │   └── braille.ts
│   ├── types/           # TypeScript type definitions
│   │   └── jszip.d.ts
│   ├── App.tsx          # Main application component
│   ├── Routes.tsx       # Routing configuration
│   ├── main.tsx         # Application entry point
│   ├── config.ts        # Configuration settings
│   └── students.ts      # Student data utilities
├── public/              # Static assets
│   └── images/
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript configuration
├── vite.config.ts       # Vite build configuration
└── index.html           # HTML template
```

## Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Build for Production**
   ```bash
   npm run build
   ```

## Features

### Core Functionality
- **Braille Processing**: Convert text to braille and display braille patterns
- **File Upload**: Drag-and-drop interface for uploading assignments and images
- **Student Management**: View and manage student profiles and progress
- **Assignment System**: Create, view, and submit educational assignments
- **Feedback System**: Provide and view feedback on student work

### UI Components
- **BrailleRenderer**: Displays braille patterns with proper formatting
- **DiagramPromptCard**: Interactive cards for diagram-based assignments
- **Dropzone**: File upload component with drag-and-drop support
- **FeedbackComposer**: Rich text editor for providing feedback

### Pages
- **Students**: Student list and profile management
- **Assignment**: Assignment creation and viewing
- **Submissions**: View and manage student submissions
- **SubmissionDetail**: Detailed view of individual submissions
- **Feedback**: Feedback management and analysis

## Development

### Technology Stack
- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Router** for navigation
- **Modern CSS** with responsive design

### Key Dependencies
- `react` - UI library
- `react-dom` - DOM rendering
- `react-router-dom` - Routing
- `typescript` - Type safety
- `vite` - Build tool

### Development Commands
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

### API Integration
The frontend communicates with the backend through service functions located in `src/services/`:
- `assignmentService.ts` - Assignment management
- `brailleService.ts` - Braille processing
- `lessonPackService.ts` - Educational content
- `studentService.ts` - Student management
- `submissionService.ts` - Submission handling

### Configuration
Environment variables and API endpoints are configured in `src/config.ts`.

## File Structure Details

### Components (`src/components/`)
Reusable UI components that can be used across different pages:
- **BrailleRenderer**: Renders braille patterns with proper spacing and formatting
- **DiagramPromptCard**: Interactive cards for diagram-based learning
- **Dropzone**: File upload component with drag-and-drop functionality
- **FeedbackComposer**: Rich text editor for providing student feedback

### Pages (`src/pages/`)
Main application views:
- **Students**: Student management interface
- **Assignment**: Assignment creation and viewing
- **Submissions**: Submission management
- **SubmissionDetail**: Detailed submission view
- **Feedback**: Feedback management

### Services (`src/services/`)
API communication layer:
- **assignmentService**: Assignment CRUD operations
- **brailleService**: Braille conversion and processing
- **lessonPackService**: Educational content management
- **studentService**: Student data management
- **submissionService**: Submission handling

### Utils (`src/utils/`)
Utility functions:
- **braille.ts**: Braille conversion utilities

### Hooks (`src/hooks/`)
Custom React hooks:
- **useGemmaTTS**: Text-to-speech functionality

## Contributing

1. Follow the existing code structure
2. Use TypeScript for all new code
3. Create reusable components when possible
4. Test your changes thoroughly
5. Update documentation as needed
