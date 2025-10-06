.. _file_management_api:

File Management API
==================

The File Management API provides a set of endpoints to list, preview, and delete uploaded files. This API is crucial for managing the documents that have been ingested into the RAG LLM application.

Data Models
-----------

**File**

A `File` object represents a single uploaded document.

.. list-table:: File Model
   :header-rows: 1
   :widths: 20 10 70

   * - Field
     - Type
     - Description
   * - `id`
     - string
     - The unique identifier for the file.
   * - `name`
     - string
     - The name of the file.
   * - `size`
     - integer
     - The size of the file in bytes.
   * - `status`
     - string
     - The processing status of the file (`processed`, `processing`, `failed`).
   * - `file_type`
     - string
     - The MIME type of the file.
   * - `ingested_at`
     - string
     - The timestamp when the file was ingested.
   * - `metadata`
     - object
     - A JSON object containing file-specific metadata (e.g., page count, chunk count, checksum).

API Endpoints
-------------

**GET /files**
~~~~~~~~~~~~~~

Lists all uploaded files with their metadata and processing status.

* **Query Parameters**:
    * `status` (string, optional): Filter by processing status (e.g., `processed`, `processing`, `failed`).
    * `file_type` (string, optional): Filter by file type (e.g., `pdf`, `docx`).
    * `limit` (integer, optional): The maximum number of files to return. Defaults to `100`.
    * `offset` (integer, optional): The pagination offset. Defaults to `0`.

* **Response**: A JSON object containing a list of `File` objects.

**GET /files/preview/{file_id}**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieves a preview of the specified file's content.

* **Path Parameter**: `file_id` (string)

* **Query Parameters**:
    * `page` (integer, optional): The page number to preview (for paginated formats). Defaults to `1`.
    * `limit` (integer, optional): The maximum number of lines or chunks to return. Defaults to `100`.

* **Response**: A JSON object containing the file's content and metadata.

**DELETE /files/{file_id}**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Deletes an uploaded file and its associated data from the system.

* **Path Parameter**: `file_id` (string)

* **Query Parameters**:
    * `force` (boolean, optional): If `true`, the file will be deleted even if it is referenced by other resources. Defaults to `false`.

* **Response**: A JSON object indicating success or failure.
