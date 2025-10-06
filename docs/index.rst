.. _top:

RAG LLM Technical Documentation
==============================

.. admonition:: Documentation Status
   :class: important

   This is the technical documentation for the RAG LLM Pipeline. The system is currently in **active development**.
   
   - **Latest Version:** 0.2.0
   - **Last Updated:** |today|

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: Getting Started
      :link: overview.html
      :link-type: doc
      :class-card: sd-outline-success
      
      New to the project? Start here to understand the system architecture and key concepts.
      
      +++
      :doc:`Overview <overview>`
      - :doc:`Architecture <architecture>`
      - :doc:`Quick Start <build_and_validation>`

   .. grid-item-card:: Core Components
      :link: ingestion_pipeline.html
      :link-type: doc
      :class-card: sd-outline-primary
      
      In-depth documentation of the system's core components.
      
      +++
      - :doc:`Ingestion Pipeline <ingestion_pipeline>`
      - :doc:`Retrieval Pipeline <retrieval_pipeline>`
      - :doc:`LLM Orchestration <llm_orchestration>`

   .. grid-item-card:: API Reference
      :class-card: sd-outline-info
      
      Complete API documentation for all modules and functions.
      
      + + + 
      - :doc:`REST API <api_reference>`
      - :doc:`WebSocket API <api_reference#websocket-interface>`
      - :doc:`Conversation API <conversation_api>`
      - :doc:`File Management API <file_management_api>`
      - :doc:`Frontend Components <frontend_components>`
      - :doc:`Configuration Reference <configuration>`

   .. grid-item-card:: Operations
      :link: operations.html
      :class-card: sd-outline-warning
      
      Deployment, monitoring, and maintenance guides.
      
      +++
      - :doc:`Deployment <operations>`
      - :doc:`Monitoring <operations#monitoring>`
      - :doc:`Troubleshooting <operations#troubleshooting>`

.. note::
   This documentation targets senior engineers integrating and operating the enterprise-grade Retrieval-Augmented Generation (RAG) pipeline. It assumes familiarity with FastAPI, LangChain, distributed systems, and observability tooling.

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Documentation
   
   overview
   architecture
   ingestion_pipeline
   retrieval_pipeline
   llm_orchestration
   api_reference
   conversation_api
   file_management_api
   frontend_components
   configuration
   operations
   testing
   changelog
   build_and_validation

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Additional Resources
   
   GitHub Repository <https://github.com/aniketsharma21/rag_llm>
   Issue Tracker <https://github.com/aniketsharma21/rag_llm/issues>
   Contributing Guide <https://github.com/aniketsharma21/rag_llm/CONTRIBUTING.md>

.. only:: html

   .. note::
      Looking for something specific? Try the :ref:`genindex` or the :ref:`search` function.

   .. toctree::
      :hidden:
      :maxdepth: 1
      :caption: Indices and Tables
      
      genindex
      search
