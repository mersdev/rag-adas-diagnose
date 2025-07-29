# Product Requirements Document: ADAS Diagnostics Co-pilot

**Version:** 1.0
**Date:** July 26, 2025
**Author:** Gemini AI
**Status:** DRAFT

## 1. Introduction

This document outlines the product requirements for the "ADAS Diagnostics Co-pilot," an AI-powered agent designed to assist automotive engineers in performing rapid root cause analysis for complex vehicle system failures.

The Co-pilot will leverage the existing Agentic RAG with Knowledge Graph platform, repurposing it for the automotive domain. It will provide a conversational interface for engineers to query technical documentation, software release notes, hardware specifications, and diagnostic logs to drastically reduce the time required to identify the root cause of in-field failures.

## 2. Problem Statement

A vehicle in the field reports a critical, intermittent failure in its Advanced Driver-Assistance System (ADAS). The diagnostics team suspects the issue could stem from a recent OTA update, a faulty sensor from a specific supplier, or an unexpected interaction between the perception and control software modules. Pinpointing the root cause requires analyzing gigabytes of logs, release notes, and hardware documentation, a process that can take days or weeks.

## 3. Product Goal & Objectives

### 3.1. Product Goal

To empower automotive diagnostics teams with an AI agent that can instantly correlate system failures with historical events and component relationships, enabling them to pinpoint the likely cause of failures in minutes, not weeks.

### 3.2. Objectives

*   **Reduce Diagnosis Time:** Decrease the average time-to-root-cause for complex ADAS failures by over 90%.
*   **Improve First-Time Fix Rate:** Increase the accuracy of initial diagnoses to ensure the correct fix is applied on the first attempt.
*   **Democratize Expertise:** Allow junior engineers to diagnose issues with a level of insight typically reserved for senior domain experts.
*   **Centralize Knowledge:** Create a single, queryable source of truth by ingesting and connecting all relevant technical and diagnostic documentation.

## 4. Target Audience

*   **Primary Persona:** Automotive Diagnostics Engineer
*   **Secondary Personas:**
    *   Functional Safety Engineer
    *   Vehicle Systems Engineer
    *   Firmware/Software Engineer

## 5. Functional Requirements

### 5.1. Data Ingestion
The system must ingest and process a corpus of automotive-specific documents, including but not limited to:
*   **Software Documentation:** OTA (Over-the-Air) update release notes, software version history, changelogs.
*   **Hardware Specifications:** Datasheets for ECUs, sensors (LiDAR, camera, radar), and other relevant hardware.
*   **System Architecture:** Design documents, interface control documents (ICDs).
*   **Diagnostic Information:** Diagnostic Trouble Code (DTC) logs, known issue databases, technician repair notes.
*   **Supplier Documentation:** Information on components provided by third-party suppliers.

### 5.2. Conversational Chat Interface (Streamlit)
The existing `cli.py` shall be deprecated and replaced by a new Streamlit-based web application (`app.py`). The interface must include:
*   A persistent chat window for user interaction.
*   A clear display area for the agent's responses, supporting markdown for formatting.
*   A mechanism to display the tools used by the agent for each query (e.g., `vector_search`, `graph_search`, `get_entity_timeline`) to provide transparency into the agent's reasoning process. This is a critical feature from the original CLI that must be retained.
*   Session management to maintain conversation context.

### 5.3. Core Agent Capabilities

**FR-1: Timeline Analysis**
*   **User Story:** As a diagnostics engineer, I want to ask for a timeline of events related to a specific vehicle system or VIN (Vehicle Identification Number) so that I can see recent changes that might have caused a failure.
*   **Details:** The agent must use the `get_entity_timeline` tool to retrieve a chronological list of software updates, hardware changes, and known issues related to the entity in the query.
*   **Example Query:** "Show the timeline of all software updates and component changes for the ADAS system in the last 60 days for VIN WXYZ123."

**FR-2: Dependency and Relationship Mapping**
*   **User Story:** As a systems engineer, I want to ask about the dependencies of a specific software or hardware component so I can understand potential interaction points and failure domains.
*   **Details:** The agent must use the `get_entity_relationships` tool to traverse the knowledge graph and display connections between components.
*   **Example Query:** "What are the documented dependencies of the 'Lane Keep Assist' module?"

**FR-3: Hybrid Search for Root Cause Hypothesis**
*   **User Story:** As a diagnostics engineer, I want to describe a failure symptom in natural language and have the agent search all relevant documents to find potential causes.
*   **Details:** The agent must use its hybrid RAG capabilities (`hybrid_search` tool) to correlate the user's description with information from release notes, known issue logs, and technical documentation.
*   **Example Query:** "The vehicle's emergency braking system is activating randomly in clear weather. What are the possible causes based on recent software updates and sensor specifications?"

## 6. Non-Functional Requirements

### 6.1. Technology Stack
*   **Language:** Python 3.11
*   **Backend API:** FastAPI (as defined in `agent/api.py`)
*   **Frontend:** Streamlit
*   **Vector Database:** PostgreSQL with pgvector extension
*   **Knowledge Graph Engine:** Neo4j
*   **Agent Framework:** Pydantic AI (as defined in `agent/agent.py`)

### 6.2. Deployment and Infrastructure
*   **Containerization:** The PostgreSQL and Neo4j databases **must** be configured to run in containers managed by **Podman**. Docker is not to be used.
*   **Deliverable:** A `podman-compose.yml` file must be provided to orchestrate the setup of the database containers.
*   **Configuration:** All connection details (database URLs, ports, credentials) must be managed through the `.env` file as per the existing project structure. The default application port should be `8058`.

### 6.3. Performance
*   **Query Response Time:** Simple queries should be answered in under 5 seconds. Complex queries requiring significant tool use should respond in under 30 seconds.
*   **Ingestion Time:** The ingestion pipeline (`ingestion/ingest.py`) must be capable of processing a 1GB corpus of documents in under 45 minutes.

### 6.4. Scalability
*   The system must be ableto handle a knowledge base of at least 10,000 documents and a knowledge graph with over 1 million nodes and relationships.

## 7. User Interface & Experience (UI/UX)

The Streamlit application (`app.py`) will serve as the primary user interface.
*   **Layout:** A two-column layout is preferred.
    *   **Left Column (or Expander):** Session information, chat history, and visualization of tools used for the last query.
    *   **Right Column (Main):** The primary chat interface.
*   **Input:** A text input box at the bottom of the main column.
*   **Output:** Responses are displayed in the main column, with markdown rendering for code blocks, lists, and tables.
*   **Transparency:** When a response is generated, the "Tools Used" section should update to show the function calls (e.g., `graph_search(query='...')`) that the agent made.

## 8. Success Metrics (KPIs)

*   **Average Time to Root Cause:** Measured before and after implementation. Target: >90% reduction.
*   **User Adoption Rate:** Percentage of diagnostics engineers using the tool weekly. Target: >70%.
*   **User Satisfaction (CSAT):** Measured via a feedback mechanism in the UI. Target: >4.5/5.
*   **Query Success Rate:** Percentage of queries that return a relevant, useful answer. Target: >85%.

## 9. Future Enhancements (Out of Scope for v1.0)

*   Ingestion of real-time vehicle telemetry data.
*   Automatic correlation of DTCs with software versions that introduced them.
*   A visual, interactive graph explorer embedded within the UI.
*   Proactive alerting for potential issues based on new software releases.