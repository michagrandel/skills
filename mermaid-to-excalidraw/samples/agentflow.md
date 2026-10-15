# Agent flow

Examples cover agent containers, task/tool/refdoc/action shapes, decisions,
metadata, normal and reference edges, and a failure path.

```mermaid
agentflow-beta TB
  request["Release brief"]@{ shape: input }
  flow writer["Writing agent"]
    draft["Draft release notes"]@{ shape: task }
    search["changelog_search"]@{ shape: tool }
    styleGuide["Tone guide"]@{ shape: refdoc }
    draft --> search
    draft -.- styleGuide
  end
  flow reviewer["Review agent"]
    check["Verify claims"]@{ shape: task }
    approved{"Approved?"}@{ shape: decision }
    revise["Revise draft"]@{ shape: task }
    check --> approved
    approved -->|No| revise
  end
  publish["Publish notes"]@{ shape: action }
  request --> writer
  writer --> reviewer
  approved -->|Yes| publish
  revise --> writer
```

```mermaid
agentflow-beta LR
  input["Customer question"]@{ shape: input }
  flow support["Support agent"]
    classify["Classify request"]@{ shape: decision }
    lookup["knowledge_base.search"]@{ shape: tool }
    answer["Compose answer"]@{ shape: task }
    classify --> lookup --> answer
  end
  send["Send response"]@{ shape: action }
  input --> support
  answer --> send
```
