# 🚀 RAG LLM Frontend

A modern, responsive web interface for the RAG (Retrieval-Augmented Generation) LLM application. Built with React and Tailwind CSS for a clean and fast user experience, and WebSockets for real-time communication.

## ✨ Features

- **Conversational Workspace**: Immersive chat layout with polished animations, responsive layouts, and accessibility-first patterns.
- **Real-time Streaming**: WebSocket-driven assistant replies with incremental rendering and graceful loading states.
- **Rich Message Experience**: Markdown rendering, inline code blocks, copy/share actions, and relative timestamps.
- **Contextual Sources**: Numbered source cards with hover states, confidence indicators, and responsive presentation.
- **Document Workbench**: Drag & drop uploads with validation, progress feedback, and toast-based alerts.
- **Conversation Intelligence**: Searchable history in the sidebar, quick filters, and persistent sessions.
- **Configurable Controls**: Settings panel for model selection and chat preferences, plus theme toggles with local persistence.

## 🚀 Recent Enhancements

- **Enhanced Components**: Rebuilt header, sidebar, chat input, message bubble, and file upload experiences (`frontend/src/components/Enhanced*.js`).
- **Advanced Search UX**: Integrated global search bar within the sidebar with focus management and filter hooks.
- **Mobile-first Polish**: Improved spacing, touch targets, and action visibility for small screens.
- **Feedback & Notifications**: Expanded toast system, inline status indicators, and consistent loading skeletons.

## 🛠️ Prerequisites

- Node.js 18+ and npm 9+
- The backend API server must be running (see the main project `README.md` for setup instructions).
- A modern web browser (e.g., Chrome, Firefox, Safari, Edge).

## 🚀 Quick Start

1.  **Navigate to the frontend directory**
    ```bash
    cd frontend
    ```

2.  **Install dependencies**
    This will install React, Tailwind CSS, and other necessary packages.
    ```bash
    npm install
    ```

3.  **Start the development server**
    ```bash
    npm start
    ```
    The application will be available at `http://localhost:3000`.

## 📦 Available Scripts

-   `npm start`: Runs the app in development mode.
-   `npm test`: Launches the test runner in interactive watch mode.
-   `npm run build`: Builds the app for production to the `build` folder.
-   `npm run eject`: Ejects the app from Create React App's managed configuration (use with caution).

## 🏗️ Project Structure

The project follows a standard Create React App structure, with components organized by feature.

```
frontend/
├── public/                # Static assets and index.html
├── src/
│   ├── components/        # Reusable React components
│   │   ├── App.js         # Main application component and routing
│   │   ├── Sidebar.js     # Left sidebar with navigation and history
│   │   ├── Header.js      # Top header with title and actions
│   │   ├── ChatWindow.js  # Container for chat messages
│   │   ├── Message.js     # Individual chat bubble component
│   │   ├── ChatInput.js   # The message input form/footer
│   │   ├── FileUpload.js  # The document upload page
│   │   └── SettingsPanel.js # The settings modal
│   ├── App.css            # Main stylesheet with Tailwind directives
│   └── index.js           # Application entry point
├── tailwind.config.js     # Tailwind CSS configuration
├── postcss.config.js      # PostCSS configuration
└── package.json           # Project dependencies and scripts
```

## 🎨 Styling

This project uses **Tailwind CSS** for all styling.

-   Utility classes are used directly in the React components.
-   The color palette, fonts, and other design tokens are defined in `tailwind.config.js`.
-   The application supports both light and dark modes, controlled by a class on the `<html>` element.

There is no need for traditional CSS files or CSS-in-JS libraries like Emotion or Material-UI.

## 🤝 Contributing

Contributions are welcome! Please follow the standard fork-and-pull-request workflow.

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/my-new-feature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/my-new-feature`).
6.  Open a Pull Request.