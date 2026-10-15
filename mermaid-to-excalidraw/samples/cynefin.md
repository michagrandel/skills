# Cynefin framework

```mermaid
cynefin-beta
  title Incident triage
  clear
    "Restart known service"
    "Apply documented fix"
  complicated
    "Analyze database latency"
    "Ask a storage expert"
  complex
    "Probe intermittent failures"
    "Run a controlled experiment"
  chaotic
    "Isolate affected region"
  confusion
    "Unknown failure mode"
  complex --> complicated : "Pattern identified"
  complicated --> clear : "Practice documented"
  chaotic --> complex : "Incident stabilized"
  clear --> chaotic : "Complacency"
```

Empty domains make a useful workshop template:

```mermaid
cynefin-beta
  title Categorize the next issue
  clear
  complicated
  complex
  chaotic
  confusion
```
