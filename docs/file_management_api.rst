.. _file_management_api:

File Management API
==================

This section documents the File Management API endpoints for the RAG LLM application.

List Uploaded Files
------------------

.. http:get:: /files

   List all uploaded files with their metadata and processing status.

   **Query Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - status
        - string
        - (Optional) Filter by status (e.g., 'processed', 'processing', 'failed')
      * - file_type
        - string
        - (Optional) Filter by file type (e.g., 'pdf', 'docx')
      * - limit
        - integer
        - (Optional) Maximum number of files to return (default: 100)
      * - offset
        - integer
        - (Optional) Pagination offset (default: 0)

   **Response**:

   .. code-block:: json

      {
        "files": [
          {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "document.pdf",
            "size": 1234567,
            "status": "processed",
            "file_type": "application/pdf",
            "ingested_at": "2025-10-07T01:42:00Z",
            "metadata": {
              "pages": 10,
              "chunks": 15,
              "checksum": "a1b2c3d4..."
            }
          }
        ],
        "total": 1,
        "limit": 100,
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
        - Server error while fetching files

Get File Preview
---------------

.. http:get:: /files/preview/{file_id}

   Get a preview of the specified file's content.

   **Path Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - file_id
        - string
        - ID of the file to preview

   **Query Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - page
        - integer
        - Page number (for paginated formats, default: 1)
      * - limit
        - integer
        - Maximum number of lines/chunks to return (default: 100)

   **Response**:

   .. code-block:: json

      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "document.pdf",
        "content": "This is the extracted text content from the first page of the document...",
        "page": 1,
        "total_pages": 10,
        "metadata": {
          "file_type": "application/pdf",
          "size": 1234567,
          "extracted_at": "2025-10-07T01:42:30Z"
        }
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
        - User not authorized to access this file
      * - 404
        - NOT_FOUND
        - File not found or not processed yet
      * - 500
        - INTERNAL_SERVER_ERROR
        - Server error while retrieving file content

Delete File
-----------

.. http:delete:: /files/{file_id}

   Delete an uploaded file and its associated data.

   **Path Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - file_id
        - string
        - ID of the file to delete

   **Query Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - force
        - boolean
        - (Optional) Force deletion even if referenced (default: false)

   **Response**:

   .. code-block:: json

      {
        "success": true,
        "message": "File deleted successfully",
        "deleted_file_id": "550e8400-e29b-41d4-a716-446655440000"
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
        - User not authorized to delete this file
      * - 404
        - NOT_FOUND
        - File not found
      * - 409
        - CONFLICT
        - File is referenced by other resources (use force=true to override)
      * - 500
        - INTERNAL_SERVER_ERROR
        - Server error while deleting file
