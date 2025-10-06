.. _frontend_components:

Frontend Components
==================

This document provides detailed documentation for the frontend components of the RAG LLM application.

.. contents:: Table of Contents
   :depth: 3
   :local:

Component Architecture
----------------------

.. mermaid::
   :align: center
   :caption: Frontend Component Architecture

   flowchart TD
       A[App] --> B[Layout]
       B --> C[Navbar]
       B --> D[Sidebar]
       B --> E[MainContent]
       E --> F[ChatInterface]
       E --> G[DocumentViewer]
       F --> H[MessageList]
       F --> I[MessageInput]
       F --> J[FileUpload]

Core Components
--------------

.. automodule:: frontend.src.components
   :members:
   :undoc-members:
   :show-inheritance:

Chat Interface
--------------

.. automodule:: frontend.src.components.ChatInterface
   :members:
   :undoc-members:
   :show-inheritance:

Document Viewer
--------------

.. automodule:: frontend.src.components.DocumentViewer
   :members:
   :undoc-members:
   :show-inheritance:

Message Components
-----------------

.. automodule:: frontend.src.components.messages
   :members:
   :undoc-members:
   :show-inheritance:

Hooks
-----

.. automodule:: frontend.src.hooks
   :members:
   :undoc-members:
   :show-inheritance:

Contexts
--------

.. automodule:: frontend.src.context
   :members:
   :undoc-members:
   :show-inheritance:

.. note::
   For implementation details of each component, refer to the source code in the `frontend/src` directory.

.. warning::
   Some components may have external dependencies. Always check the `package.json` for version requirements.

.. seealso::
   - :doc:`api_reference` for backend API documentation
   - :doc:`configuration` for frontend configuration options
