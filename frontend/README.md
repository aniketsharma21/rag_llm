# 🚀 RAG LLM Frontend

A modern, responsive web interface for the RAG (Retrieval-Augmented Generation) LLM application. Built with React and Tailwind CSS for a clean and fast user experience, and WebSockets for real-time communication.

## ✨ Features

- **Modern Chat Interface**: A clean, bubble-style UI for conversations.
- **Real-time Message Streaming**: Bot responses are streamed in real-time.
- **Markdown Rendering**: Messages are rendered with Markdown support.
- **Source Attribution**: Bot messages can display the sources used for generation.
- **Message Feedback**: Users can provide "helpful" or "not helpful" feedback on bot responses.
- **Conversation History**: Past conversations are saved and can be revisited.
- **Document Upload**: A dedicated page for uploading PDF documents to the knowledge base.
- **Customizable Settings**: A modal to configure the AI model and other parameters.
- **Responsive Design**: The UI is optimized for both desktop and mobile devices.
- **Light/Dark Mode**: Toggle between light and dark themes, with the user's preference saved locally.

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