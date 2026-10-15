# Entity relationship diagrams

The first example intentionally covers the full set of Mermaid ER endpoint
markers on six relationship lines: exactly one (`||`), zero-or-one (`o|`),
one-or-more (`|{`), and zero-or-more (`o{`). It also includes composite keys,
foreign keys, several data types, and an attribute comment.

```mermaid
erDiagram
  ACCOUNT ||--|| PROFILE : owns
  ACCOUNT ||--o| PREFERENCE : configures
  ACCOUNT ||--|{ SESSION : opens
  ACCOUNT ||--o{ UPLOAD : creates
  TEAM o|--o{ ACCOUNT : includes
  ASSET }o--o{ LABEL : tagged_with

  ACCOUNT {
    uuid id PK
    varchar(120) email UK "Login address; kept lowercase"
    timestamp created_at
    boolean is_active
  }
  PROFILE {
    uuid account_id PK, FK
    varchar(80) display_name
    text biography "Optional public description"
    date birth_date
  }
  PREFERENCE {
    uuid account_id PK, FK
    json settings
    varchar(10) locale
  }
  SESSION {
    uuid id PK
    uuid account_id FK
    timestamp expires_at
    inet ip_address
  }
  UPLOAD {
    bigint id PK
    uuid account_id FK
    decimal size_mb
    blob checksum
  }
  TEAM {
    int id PK
    varchar(100) name UK
  }
  ASSET {
    uuid id PK
    uuid owner_id FK
    text uri
  }
  LABEL {
    int id PK
    varchar(50) name UK
  }
```

The second example adds mandatory many-to-many links, a self-reference, and
named attributes with notes:

```mermaid
erDiagram
  PROJECT ||--|{ TASK : contains
  TASK ||--o{ TASK : parent_of
  USER ||--o{ TASK : assigned
  TASK }|--|{ COMPONENT : uses

  PROJECT {
    int id PK
    varchar(160) name
    date started_on
  }
  TASK {
    uuid id PK
    int project_id FK
    uuid parent_id FK "Null for a root task"
    uuid assignee_id FK
    enum status
    datetime due_at
  }
  USER {
    uuid id PK
    varchar(254) email UK
  }
  COMPONENT {
    int id PK
    varchar(80) name
  }
```
