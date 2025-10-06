.. _conversation_api:

Conversation Management API
===========================

This section documents the Conversation Management API endpoints for the RAG LLM application.

List Conversations
------------------

.. http:get:: /conversations

   List all conversations for a user with pagination support.

   **Query Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - user_id
        - string
        - (Optional) User ID (default: "default_user")
      * - limit
        - integer
        - (Optional) Maximum number of conversations to return (default: 50)
      * - offset
        - integer
        - (Optional) Pagination offset (default: 0)

   **Response**:

   .. code-block:: json

      {
        "conversations": [
          {
            "id": 1,
            "title": "Conversation about RAG",
            "created_at": "2025-10-07T01:42:00Z",
            "updated_at": "2025-10-07T01:43:30Z",
            "message_count": 5
          }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0
      }

   **Error Responses**:

   .. list-table:: Error Responses
      :header-rows: 1
      :widths: 15 15 70

      * - Status Code
        - Error Code
        - Description
      * - 401
        - UNAUTHORIZED
        - Missing or invalid authentication
      * - 500
        - INTERNAL_SERVER_ERROR
        - Server error while fetching conversations

Get Conversation
---------------

.. http:get:: /conversations/{conversation_id}

   Get details of a specific conversation including its messages.

   **Path Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - conversation_id
        - integer
        - ID of the conversation to retrieve

   **Response**:

   .. code-block:: json

      {
        "id": 1,
        "title": "Conversation about RAG",
        "user_id": "default_user",
        "created_at": "2025-10-07T01:42:00Z",
        "updated_at": "2025-10-07T01:43:30Z",
        "messages": [
          {
            "id": 1,
            "content": "What is RAG?",
            "role": "user",
            "created_at": "2025-10-07T01:42:10Z"
          },
          {
            "id": 2,
            "content": "RAG (Retrieval-Augmented Generation) is...",
            "role": "assistant",
            "created_at": "2025-10-07T01:42:15Z"
          }
        ]
      }

   **Error Responses**:

   .. list-table:: Error Responses
      :header-rows: 1
      :widths: 15 15 70

      * - Status Code
        - Error Code
        - Description
      * - 401
        - UNAUTHORIZED
        - Missing or invalid authentication
      * - 404
        - NOT_FOUND
        - Conversation not found
      * - 500
        - INTERNAL_SERVER_ERROR
        - Server error while fetching conversation

Create Conversation
------------------

.. http:post:: /conversations

   Create a new conversation.

   **Request Body**:

   .. list-table:: Fields
      :header-rows: 1
      :widths: 20 10 70

      * - Field
        - Type
        - Description
      * - title
        - string
        - Title for the conversation
      * - user_id
        - string
        - (Optional) User ID (default: "default_user")

   **Request Example**:

   .. code-block:: json

      {
        "title": "New Conversation",
        "user_id": "user123"
      }

   **Response**:

   .. code-block:: json

      {
        "id": 2,
        "title": "New Conversation",
        "user_id": "user123",
        "created_at": "2025-10-07T02:00:00Z",
        "updated_at": "2025-10-07T02:00:00Z",
        "messages": []
      }

   **Error Responses**:

   .. list-table:: Error Responses
      :header-rows: 1
      :widths: 15 15 70

      * - Status Code
        - Error Code
        - Description
      * - 400
        - VALIDATION_ERROR
        - Invalid request body
      * - 401
        - UNAUTHORIZED
        - Missing or invalid authentication
      * - 500
        - INTERNAL_SERVER_ERROR
        - Server error while creating conversation

Delete Conversation
------------------

.. http:delete:: /conversations/{conversation_id}

   Delete a conversation and all its messages.

   **Path Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - conversation_id
        - integer
        - ID of the conversation to delete

   **Response**:

   .. code-block:: json

      {
        "success": true,
        "message": "Conversation deleted successfully"
      }

   **Error Responses**:

   .. list-table:: Error Responses
      :header-rows: 1
      :widths: 15 15 70

      * - Status Code
        - Error Code
        - Description
      * - 401
        - UNAUTHORIZED
        - Missing or invalid authentication
      * - 403
        - FORBIDDEN
        - User not authorized to delete this conversation
      * - 404
        - NOT_FOUND
        - Conversation not found
      * - 500
        - INTERNAL_SERVER_ERROR
        - Server error while deleting conversation
