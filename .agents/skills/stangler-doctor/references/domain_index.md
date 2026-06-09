# Domain Index — Reference Corpus

This index maps 13 technical domains across 37 reference files.
**Read only the file(s) relevant to your current task.**

All files are co-located in this skill's `references/` directory.
Path: `.agents/skills/stangler-doctor/references/`

### Additional References (Skill-Specific)
| File | Purpose |
|------|---------|
| `adr_template.md` | ADR template for Turn 1 planning |
| `project_layout.md` | Standard Hexagonal project directory structure |
| `mutmut_guide.md` | How to run and interpret mutation testing results |
| `adr_lifecycle_guide.md` | Governance, state transitions, and resolution of impasses |
| `legacy_strangling_patterns.md` | Anti-Corruption Layer (ACL) isolation patterns for non-conformant code |
| `zero_downtime_migrations.md` | Unifying schema evolution with the ADR lifecycle using Expand-Contract patterns |

---

## Domain 01: Computing Fundamentals and Servers
**When to consult:** Server architecture decisions, networking, OS-level concerns, compute resource planning.

| File | Size | Key Topics |
|------|------|------------|
| `1-01 Computing Fundamentals and Servers 1.md` | 474KB | Server architecture, networking fundamentals, OS internals, compute patterns, MLOps infrastructure best practices |
| `2-01 Computing Fundamentals and Servers 2.md` | 405KB | Advanced server patterns, scaling strategies, performance tuning, distributed systems fundamentals |

---

## Domain 02: Programming and Backend Development
**When to consult:** Python patterns, backend architecture, API design, OPA/ABAC authorization, clean code.

| File | Size | Key Topics |
|------|------|------------|
| `3-02 Programming and Backend Development 1.md` | 478KB | ABAC with OPA, authorization patterns, Python backend architecture, API security models |
| `4-02 Programming and Backend Development 2.md` | 456KB | Advanced Python patterns, backend optimization, service design, code quality practices |
| `5-02 Programming and Backend Development 3.md` | 25KB | Supplementary backend patterns, edge cases, specialized techniques |

---

## Domain 03: Databases, Queues, and Cache
**When to consult:** PostgreSQL, Redis, message queues, caching strategies, data persistence patterns.

| File | Size | Key Topics |
|------|------|------------|
| `6-03 Databases, Queues, and Cache 1.md` | 476KB | Container security for data services, database hardening, PostgreSQL patterns, cache architecture |
| `7-03 Databases, Queues, and Cache 2.md` | 274KB | Queue systems, Redis patterns, cache invalidation strategies, data replication |

---

## Domain 04: Containers, Docker, and Orchestration
**When to consult:** Dockerfile optimization, docker-compose patterns, Kubernetes deployment, cluster management.

| File | Size | Key Topics |
|------|------|------------|
| `8-04 Containers, Docker, and Orchestration 1.md` | 472KB | Kubernetes 2026 playbook, AI at scale, self-healing clusters, container orchestration patterns |
| `9-04 Containers, Docker, and Orchestration 2.md` | 158KB | Advanced Docker patterns, multi-stage builds, orchestration edge cases |

---

## Domain 05: AI and Machine Learning Fundamentals
**When to consult:** ML model design, training pipelines, evaluation metrics, statistical methods, data science.

| File | Size | Key Topics |
|------|------|------------|
| `10-05 IA and Machine Learning Fundamentals 1.md` | 482KB | Monte Carlo methods, conformal prediction, uncertainty quantification, model evaluation |
| `11-05 IA and Machine Learning Fundamentals 2.md` | 479KB | Feature engineering, model selection, training optimization, ML pipelines |
| `12-05 IA and Machine Learning Fundamentals 3.md` | 479KB | Advanced ML techniques, ensemble methods, hyperparameter tuning |
| `13-05 IA and Machine Learning Fundamentals 4.md` | 71KB | Supplementary ML concepts, specialized algorithms |

---

## Domain 06: Deep Learning and Modern Architectures
**When to consult:** Neural network design, transformers, attention mechanisms, CNN/RNN, model architecture decisions.

| File | Size | Key Topics |
|------|------|------------|
| `14-06 Deep Learning and Modern Architectures 1.md` | 481KB | Deep learning foundations, neural network architectures, backpropagation, optimization |
| `15-06 Deep Learning and Modern Architectures 2.md` | 480KB | Transformer architectures, attention mechanisms, modern DL patterns |
| `16-06 Deep Learning and Modern Architectures 3.md` | 480KB | CNN, RNN, LSTM, sequence models, generative architectures |
| `17-06 Deep Learning and Modern Architectures 4.md` | 343KB | Advanced architectures, diffusion models, multimodal systems |
| `18-06 Deep Learning and Modern Architectures 5.md` | 15KB | Supplementary deep learning topics |

---

## Domain 07: Framework Ecosystem and Model Tools
**When to consult:** TensorFlow vs PyTorch decisions, framework selection, model serving tools, training frameworks.

| File | Size | Key Topics |
|------|------|------------|
| `19-07 Framework Ecosystem and Model Tools 1.md` | 476KB | TensorFlow, PyTorch comparison, framework selection criteria, deep learning frameworks 2025 |
| `20-07 Framework Ecosystem and Model Tools 2.md` | 322KB | Model serving tools, ONNX, TensorRT, deployment frameworks |

---

## Domain 08: MLOps and LLMOps
**When to consult:** ML pipeline automation, model versioning, experiment tracking, LLM deployment, structured outputs.

| File | Size | Key Topics |
|------|------|------------|
| `21-08 MLOps and LLMOps 1.md` | 475KB | Structured LLM outputs, Python tools comparison, MLOps pipeline patterns |
| `22-08 MLOps and LLMOps 2.md` | 423KB | LLMOps practices, model monitoring, A/B testing, experiment tracking |

---

## Domain 09: AI and LLM System Architecture
**When to consult:** RAG pipelines, LLM system design, prompt engineering, agent architectures, embedding strategies.

| File | Size | Key Topics |
|------|------|------------|
| `23-09 AI and LLM System Architecture 1.md` | 474KB | Advanced RAG techniques (9 methods), hybrid search, semantic retrieval, re-ranking |
| `24-09 AI and LLM System Architecture 2.md` | 424KB | LLM system design, agent architectures, prompt patterns, production LLM systems |

---

## Domain 10: Automation and Integration
**When to consult:** Ports & Adapters implementation, integration patterns, web scraping, API integration, workflow automation.

| File | Size | Key Topics |
|------|------|------------|
| `25-10 Automation, and Integration 1.md` | 468KB | Ports & Adapters architecture deep-dive, Hexagonal implementation patterns |
| `26-10 Automation, and Integration 2.md` | 336KB | Web scraping (Playwright, BeautifulSoup4), API integration, workflow automation |

---

## Domain 11: Container-Infra Security
**When to consult:** Container hardening, supply chain security, image scanning, runtime protection, DevSecOps.

| File | Size | Key Topics |
|------|------|------------|
| `27-11 Container-Infra Security 1.md` | 476KB | MLOps security best practices, container hardening, supply chain security |
| `28-11 Container-Infra Security 2.md` | 153KB | Runtime security, image scanning, Snyk/SonarQube integration |

---

## Domain 12: Observability and Operation
**When to consult:** Logging, monitoring, tracing, Prometheus/Grafana setup, Kubernetes observability, SRE practices.

| File | Size | Key Topics |
|------|------|------------|
| `29-12 Observability and Operation 1.md` | 365KB | Kubernetes logging best practices, vCluster, log aggregation patterns |
| `30-12 Observability and Operation 2.md` | 480KB | Prometheus, Grafana dashboards, alerting, distributed tracing |
| `31-12 Observability and Operation 3.md` | 78KB | SRE practices, incident management, post-mortem templates |

---

## Domain 13: Cloud and Hardware for AI
**When to consult:** Cloud provider selection (AWS/GCP/Azure), GPU/TPU strategies, Pulumi/Terraform IaC, cost optimization.

| File | Size | Key Topics |
|------|------|------------|
| `32-13 Cloud and Hardware for AI 1.md` | 479KB | GKE, HITRUST compliance, Pulumi best practices, cloud REST APIs |
| `33-13 Cloud and Hardware for AI 2.md` | 479KB | Multi-cloud strategies, cloud-native patterns, hybrid deployments |
| `34-13 Cloud and Hardware for AI 3.md` | 478KB | GPU/TPU provisioning, AI hardware optimization, cost management |
| `35-13 Cloud and Hardware for AI 4.md` | 480KB | Advanced cloud patterns, serverless AI, edge computing |
| `36-13 Cloud and Hardware for AI 5.md` | 293KB | Supplementary cloud topics, vendor comparisons |

---

## Meta: Codified Methodology
**When to consult:** ADR templates, TDD protocol details, the complete Stangler Method specification.

| File | Size | Key Topics |
|------|------|------------|
| `37-DevOps, DDD, TDD, ADRs, Code.md` | 17KB | Complete Stangler Method, ADR→TDD→Code protocol, 5 Pillars, defensive engineering rules |
