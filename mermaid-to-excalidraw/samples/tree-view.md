# Tree view diagrams

```mermaid
treeView-beta
  texture-pipeline/
    src/
      importer/
        scanner.py
        metadata.py
      catalog/
        models.py
    tests/
      test_scanner.py
    README.md
```

Quoted names, descriptions, highlights, and box-drawing input:

```mermaid
treeView-beta
  project/
    docs/
      plans/
        "00-pipeline.md" ## overview
        "01-catalog.md" :::highlight ## catalog design
    assets/
      "sample texture.png"
    pyproject.toml ## dependencies
```

```mermaid
treeView-beta
├── src/
│   ├── app.py ## entry point
│   └── config.py
├── tests/
│   └── test_app.py
└── README.md
```
