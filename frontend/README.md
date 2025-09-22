# 🚀 RAG LLM Frontend

A modern, responsive web interface for the RAG (Retrieval-Augmented Generation) LLM application. Built with React, Material-UI, and WebSockets for real-time communication.

## ✨ Features

- **Interactive Chat Interface**
  - Real-time message streaming
  - Markdown support for rich text rendering
  - Source attribution for answers
  - Message history and persistence

- **Document Management**
  - Drag-and-drop file upload
  - Support for multiple document formats (PDF, DOCX, TXT)
  - Document preview and management
  - Upload progress tracking

- **User Experience**
  - Responsive design for all devices
  - Dark/light theme support
  - Keyboard shortcuts
  - Loading states and error handling
  - Enhanced sidebar and navigation (2025-09-22)
  - Improved chat and document management UX (2025-09-22)
  - Routing with `react-router-dom` (2025-09-22)

- **Developer Experience**
  - TypeScript support
  - Comprehensive documentation
  - Unit and integration testing
  - Code quality tools (ESLint, Prettier)

## 🛠️ Prerequisites

- Node.js 18+ and npm 9+ or yarn
- Backend API server (see main [README](../README.md) for setup)
- Modern web browser (Chrome, Firefox, Safari, Edge)

## 🚀 Quick Start

1. **Clone the repository** (if not already done)
   ```bash
   git clone <repository-url>
   cd rag_llm/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Install routing dependency**
   ```bash
   npm install react-router-dom
   ```

4. **Start the development server**
   ```bash
   npm start
   # or
   yarn start
   ```
   The application will be available at [http://localhost:3000](http://localhost:3000)

## 🆕 Recent Updates (2025-09-22)
- Enhanced sidebar and navigation for better usability.
- Improved chat and document management experience.
- Added `react-router-dom` for client-side routing.

## 📦 Available Scripts

- `npm start` - Start the development server
- `npm test` - Run tests in watch mode
- `npm run build` - Create a production build
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier
- `npm run type-check` - Check TypeScript types
- `npm run analyze` - Analyze bundle size

## 🏗️ Project Structure

```
frontend/
├── public/                # Static assets
│   ├── index.html         # HTML template
│   └── assets/            # Images, fonts, etc.
├── src/
│   ├── assets/            # Static assets (images, icons, etc.)
│   ├── components/        # Reusable UI components
│   │   ├── chat/          # Chat-related components
│   │   ├── documents/     # Document management components
│   │   ├── layout/        # Layout components
│   │   └── ui/            # Generic UI components
│   ├── contexts/          # React contexts
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API and WebSocket services
│   ├── store/             # State management
│   ├── theme/             # MUI theme configuration
│   ├── types/             # TypeScript type definitions
│   ├── utils/             # Utility functions
│   ├── App.tsx            # Main application component
│   ├── index.tsx          # Application entry point
│   └── routes.tsx         # Application routes
├── .env.example          # Example environment variables
├── package.json          # Dependencies and scripts
└── tsconfig.json         # TypeScript configuration
```

## 🎨 Styling

This project uses:
- [Emotion](https://emotion.sh/) for component styling
- [Material-UI](https://mui.com/) for UI components
- CSS Modules for scoped styles

### Theming

Customize the theme in `src/theme/theme.ts`. The application supports:
- Light and dark modes
- Custom color palettes
- Responsive typography
- Component overrides

## 🌐 API Integration

API calls are managed through:
- `src/services/api.ts` - REST API client
- `src/services/websocket.ts` - WebSocket client

### Making API Calls

```typescript
import api from '../services/api';

// Example API call
const fetchDocuments = async () => {
  try {
    const response = await api.get('/documents');
    return response.data;
  } catch (error) {
    console.error('Error fetching documents:', error);
    throw error;
  }
};
```

## 🧪 Testing

Run tests with:
```bash
npm test
# or
yarn test
```

Test files should be named `*.test.tsx` or `*.spec.tsx` and placed next to the components they test.

## 🚀 Deployment

### Production Build

Create an optimized production build:
```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

### Docker

Build and run with Docker:
```bash
docker build -t rag-llm-frontend .
docker run -p 3000:80 rag-llm-frontend
```

### Static File Server

Serve the production build using a static file server:
```bash
npx serve -s build -l 3000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 📚 Resources

- [React Documentation](https://reactjs.org/)
- [Material-UI Documentation](https://mui.com/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Create React App Documentation](https://create-react-app.dev/)
