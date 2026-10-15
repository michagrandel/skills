# Sequence diagrams

```mermaid
sequenceDiagram
  actor User
  participant UI as Desktop UI
  participant API as Catalog API
  database DB as Catalog DB
  User->>UI: Search for a texture
  activate UI
  UI->>+API: GET /assets?q=wood
  API->>+DB: Query indexed metadata
  DB-->>-API: Matching asset rows
  API-->>-UI: Results and thumbnails
  UI-->>User: Display result grid
  deactivate UI
```

Alternatives, optional work, loops, notes, and asynchronous messages:

```mermaid
sequenceDiagram
  participant UI
  participant Importer
  participant Worker
  UI->>Importer: Start folder scan
  alt Folder is readable
    loop For each image
      Importer->>Worker: Queue thumbnail job
      Worker-->>Importer: Thumbnail ready
    end
    Importer-->>UI: Import complete
  else Permission denied
    Importer-->>UI: Show access error
  end
  opt User opens diagnostics
    UI->>Importer: Get scan summary
    Importer-->>UI: Counts and warnings
  end
  Note over UI,Worker: Jobs may finish out of order
```
