.. _frontend_components:

Frontend Components
==================

This document provides an overview of the key React components that make up the RAG LLM application's frontend.

Component Architecture
----------------------

The frontend is built with React and Tailwind CSS, following a component-based architecture. The main components work together to provide a seamless user experience.

.. mermaid::
   :align: center
   :caption: Frontend Component Architecture

   graph TD
       A[App] --> B[Layout];
       B --> C[Navbar];
       B --> D[Sidebar];
       B --> E[MainContent];
       E --> F[ChatInterface];
       E --> G[DocumentViewer];
       F --> H[MessageList];
       F --> I[MessageInput];
       F --> J[EnhancedFileUpload];

Core Components
---------------

**App.js**

The root component of the application, responsible for:

*   Initializing the main layout.
*   Managing application-level state through the `ConfigContext`.
*   Routing between different views (e.g., chat, document upload).

**ChatInterface.js**

This component provides the main chat interface for users to interact with the RAG model.

*   **Props**: None
*   **State**: Manages the current conversation, including messages and user input.
*   **Functionality**: Handles WebSocket communication for real-time chat, sends user queries to the backend, and displays the model's responses.

**EnhancedFileUpload.js**

A sophisticated file upload component that supports drag-and-drop and provides feedback on the upload process.

*   **Props**: `onUploadComplete` (function)
*   **State**: Manages the list of uploaded files, their upload status, and any errors.
*   **Functionality**: Communicates with the `/ingest` and `/status` endpoints to upload files and monitor their processing.

**EnhancedMessage.js**

Displays a single message in the chat interface, with special rendering for sources and citations.

*   **Props**: `message` (object)
*   **Functionality**: Renders user and assistant messages, formats citations as superscripts, and displays source cards with document previews.

Hooks and Context
-----------------

**useWebSocket.js**

A custom hook that encapsulates the logic for managing the WebSocket connection to the backend.

*   **Returns**: An object with the connection status, the latest message, and a function to send messages.
*   **Functionality**: Handles connection, disconnection, and message-passing events.

**ConfigContext.js**

A React context that provides application-wide configuration to all components.

*   **Value**: An object containing the WebSocket and API endpoints.
*   **Functionality**: Allows components to access the backend URLs without hardcoding them.
