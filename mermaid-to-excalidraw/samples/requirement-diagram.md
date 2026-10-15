# Requirement diagrams

```mermaid
requirementDiagram
  requirement image_quality {
    id: REQ-1
    text: Imported images must retain their original dimensions.
    risk: medium
    verifymethod: test
  }
  functionalRequirement thumbnail {
    id: REQ-2
    text: The system shall generate a preview for each supported image.
    risk: low
    verifymethod: demonstration
  }
  element import_service {
    type: service
  }
  import_service - satisfies -> image_quality
  import_service - refines -> thumbnail
  thumbnail - derives -> image_quality
```

Containment and verification relations:

```mermaid
requirementDiagram
  performanceRequirement search_latency {
    id: PERF-3
    text: Search results must appear within 300 milliseconds.
    risk: high
    verifymethod: test
  }
  designConstraint local_storage {
    id: CON-4
    text: The catalog database must remain local to the workstation.
    risk: medium
    verifymethod: inspection
  }
  element search_index {
    type: component
  }
  search_index - satisfies -> search_latency
  search_index - verifies -> local_storage
```
