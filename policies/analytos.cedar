version: 1

groups:
  reviewer: ["reviewer-demo", "reviewer-aswini", "reviewer-system"]
  content-agent: ["content-agent"]
  gtm-agent: ["gtm-agent"]
  dashboard-reader: ["dashboard-reader"]
  ingestion-service: ["ingestion-service"]

rules:
  - id: reviewers-read-main-and-branches
    allow:
      actors:
        group: reviewer
      actions: [read, export, invoke_query]

  - id: reviewers-manage-ingestion-branches
    allow:
      actors:
        group: reviewer
      actions: [branch_merge, branch_delete]

  - id: content-agent-read-main
    allow:
      actors:
        group: content-agent
      actions: [read, export]

  - id: gtm-agent-read-main
    allow:
      actors:
        group: gtm-agent
      actions: [read, export]

  - id: dashboard-reader-read-main
    allow:
      actors:
        group: dashboard-reader
      actions: [read, export]

  - id: agents-and-dashboard-invoke-stored-queries
    allow:
      actors:
        group: content-agent
      actions: [invoke_query]

  - id: gtm-agent-invoke-stored-queries
    allow:
      actors:
        group: gtm-agent
      actions: [invoke_query]

  - id: dashboard-reader-invoke-stored-queries
    allow:
      actors:
        group: dashboard-reader
      actions: [invoke_query]

  - id: ingestion-service-creates-branches
    allow:
      actors:
        group: ingestion-service
      actions: [branch_create]
