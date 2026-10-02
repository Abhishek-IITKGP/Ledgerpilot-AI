# FinSight AI Architecture Diagrams

Four diagrams plus an editable database-design deck, for different audiences:

1. [Technical runtime and API flow](01-technical-flow.md) covers the layers,
   all API endpoints, the deterministic and AI paths, RAG, audit, approval,
   roles, and the 22 tables in the four application schemas.
2. [Database ERD and data workflow](02-database-design.md) shows the live
   PostgreSQL tables and declared PK/FK relationships, then explains the
   financial investigation, explanation/RAG, and approval data paths.
3. [POC functional flow](03-poc-functional-flow.md) tells the operational
   story without requiring the audience to know FastAPI, SQL, or model APIs.
4. [Core API map](04-core-api-map.md) shows how the endpoints fit the case
  workflow and why each API matters.
5. [Database design PowerPoint](finsight-database-design.pptx) is a three-slide
  deck with the four-schema overview, financial FK chain, and investigation / AI / approval data flow.

## View and present

- Open a Markdown file and use **Ctrl+Shift+V** for the VS Code Markdown
  preview. GitHub also renders the Mermaid diagrams.
- For PowerPoint, insert
  [the 16:9 SVG](assets/finsight-poc-functional-flow.svg) with **Insert >
  Pictures**. It is a vector graphic, so it remains crisp when resized.
- The [core API SVG](assets/finsight-core-apis.svg) is another 16:9 vector
  slide, focused on endpoint responsibilities and user value.
- Regenerate the editable database deck with
  `python docs/architecture/tools/create_database_design_ppt.py`. It uses
  `python-pptx` and is built from PowerPoint shapes and text, not a flattened
  image.
- The technical and database diagrams are deliberately detailed and work best
  zoomed or exported on a wide page. Use the POC SVG for a live presentation.

## Accuracy notes

- The database design was checked against the configured PostgreSQL catalog.
  It covers 22 tables in `authentication`, `financial`, `investigation`, and
  `ai`. Base financial/authentication provisioning is not fully represented by
  migrations in this repository.
- The current stable demo uses `AI_PROVIDER=mock`. The LLM provider and lexical
  RAG path are implemented, but live Gemini has had intermittent `503`
  availability errors.
- The example policy documents are demonstration content only; replace them
  with organization-approved material before operational use.