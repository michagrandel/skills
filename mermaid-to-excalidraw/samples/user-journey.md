# User journey diagrams

```mermaid
journey
  title Import and organize a texture
  section Find files
    Locate source folder: 4: Artist
    Check supported formats: 3: Artist
  section Import
    Choose scan options: 4: Artist
    Wait for thumbnails: 2: Artist, System
    Review warnings: 3: Artist
  section Organize
    Add tags: 5: Artist
    Save collection: 4: Artist
```

Multiple actors and a frustration point:

```mermaid
journey
  title Resolve a duplicate image
  section Detect
    Run duplicate scan: 4: Artist, System
    Inspect matching files: 3: Artist
  section Decide
    Compare metadata: 2: Artist
    Keep preferred source: 5: Artist
  section Finish
    Confirm cleanup: 4: Artist, System
```
