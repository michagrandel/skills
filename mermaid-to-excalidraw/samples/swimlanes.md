# Swimlane diagrams

```mermaid
swimlane-beta LR
  subgraph Customer
    request[Submit image folder]
    review[Review imported assets]
  end
  subgraph Desktop
    choose[Choose import options]
    summarize[Show import summary]
  end
  subgraph Catalog
    scan[Scan source files]
    index[Write metadata]
  end
  request --> choose --> scan --> index --> summarize --> review
```

Decisions, labeled handoffs, and a retry loop:

```mermaid
swimlane-beta LR
  subgraph Artist
    upload[Select folder]
    confirm[Confirm results]
  end
  subgraph Importer
    inspect{Files readable?}
    retry[Request a new folder]
    import[Import files]
  end
  upload --> inspect
  inspect -->|Yes| import --> confirm
  inspect -->|No| retry --> upload
```
