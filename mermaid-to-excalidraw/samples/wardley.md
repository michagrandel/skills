# Wardley maps

```mermaid
wardley-beta
title Texture catalog value chain
anchor Artist [0.92, 0.88]
component Search [0.75, 0.68]
component Catalog [0.62, 0.48]
component Image processing [0.48, 0.31]
component Local storage [0.35, 0.82]

Artist -> Search
Search -> Catalog
Catalog -> Image processing
Catalog -> Local storage
evolve Image processing 0.55
note "Improve previews before scaling imports" [0.38, 0.55]
```

Sourcing decorators and labeled dependencies:

```mermaid
wardley-beta
title Build or buy
anchor Team [0.88, 0.90]
component Desktop client [0.73, 0.62] (build)
component Search engine [0.64, 0.78] (buy)
component File system [0.42, 0.95] (market)
component Legacy importer [0.50, 0.25] (inertia)

Team -> Desktop client
Desktop client -> Search engine; query API
Desktop client -> File system
Desktop client -.-> Legacy importer
```
