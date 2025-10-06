.. _conversation_api:

Conversation Management API
===========================

The Conversation Management API provides a set of endpoints to create, retrieve, and manage conversations within the RAG LLM application. This API is essential for maintaining conversation history and enabling multi-turn interactions.

Data Models
-----------

**Conversation**

A `Conversation` object represents a single conversation thread.

.. list-table:: Conversation Model
   :header-rows: 1
   :widths: 20 10 70

   * - Field
     - Type
     - Description
   * - `id`
     - integer
     - The unique identifier for the conversation.
   * - `title`
     - string
     - The title of the conversation.
   * - `user_id`
     - string
     - The ID of the user who owns the conversation.
   * - `created_at`
     - string
     - The timestamp when the conversation was created.
   * - `updated_at`
     - string
     - The timestamp when the conversation was last updated.
   * - `messages`
     - array
     - An array of `Message` objects associated with the conversation.

**Message**

A `Message` object represents a single message within a conversation.

.. list-table:: Message Model
   :header-rows: 1
   :widths: 20 10 70

   * - Field
     - Type
     - Description
   * - `id`
     - integer
     - The unique identifier for the message.
   * - `content`
     - string
     - The content of the message.
   * - `role`
     - string
     - The role of the message sender (`user` or `assistant`).
   * - `created_at`
     - string
     - The timestamp when the message was created.

API Endpoints
-------------

**GET /conversations**
~~~~~~~~~~~~~~~~~~~~~~

Lists all conversations for a user with pagination support.

* **Query Parameters**:
    * `user_id` (string, optional): The ID of the user. Defaults to `default_user`.
    * `limit` (integer, optional): The maximum number of conversations to return. Defaults to `50`.
    * `offset` (integer, optional): The pagination offset. Defaults to `0`.

* **Response**: A JSON object containing a list of `Conversation` objects.

**GET /conversations/{conversation_id}**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieves the details of a specific conversation, including its messages.

* **Path Parameter**: `conversation_id` (integer)

* **Response**: A `Conversation` object.

**POST /conversations**
~~~~~~~~~~~~~~~~~~~~~~~

Creates a new conversation.

* **Request Body**: A JSON object with a `title` (string) and an optional `user_id` (string).

* **Response**: The newly created `Conversation` object.

**DELETE /conversations/{conversation_id}**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Deletes a conversation and all its associated messages.

* **Path Parameter**: `conversation_id` (integer)

* **Response**: A JSON object indicating success or failure.
