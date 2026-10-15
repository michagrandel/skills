# Use case diagrams

```mermaid
usecase-beta
direction LR
actor Artist("Texture artist")
actor Admin("Catalog administrator")
systemBoundary Catalog
  Browse("Browse assets")
  Search("Search by tag")
  Import("Import folder")
  Manage("Manage users")
end
Artist --> Browse
Artist --> Search
Artist --> Import
Admin --> Manage
Import ..> : include Browse
```

Actor variants, business use cases, extensions, and another boundary:

```mermaid
usecase-beta
direction TB
actor Customer("Customer")
actor Reviewer("Reviewer")@{ type: hollow }
systemBoundary Library
  Download("Download asset")
  Preview("Preview asset")
  Report("Report metadata issue")
end
Customer --> Download
Customer --> Preview
Reviewer --> Report
Report ..> Download : extend
```
