param(
    [string]$ApiUrl = "http://127.0.0.1:8000",
    [string]$Reviewer = "reviewer-aswini"
)

$ErrorActionPreference = "Stop"

$seedFiles = @(
    "seed-data/stockly-product-overview.md",
    "seed-data/inspectly-product-overview.md",
    "seed-data/icp-analytos.md",
    "seed-data/email-01-stockly-pilot-thread.md",
    "seed-data/email-02-inspectly-medical-thread.md"
)

Write-Host "This helper uses the governed API flow only. It does not reset real main."
Write-Host "Back up or reset the graph manually before running if you need an empty main."

$runs = @()
foreach ($path in $seedFiles) {
    $body = @{ source_path = $path; actor = "ingestion-service"; extraction_provider = "rule-based" } | ConvertTo-Json
    $run = Invoke-RestMethod -Method Post -Uri "$ApiUrl/ingestions" -ContentType "application/json" -Body $body
    $runs += $run
    Write-Host "Created review $($run.run_id) on $($run.branch_name)"
}

$pending = Invoke-RestMethod -Method Get -Uri "$ApiUrl/reviews"
Write-Host "Pending reviews: $($pending.Count)"

foreach ($run in $runs) {
    $diff = Invoke-RestMethod -Method Get -Uri "$ApiUrl/reviews/$($run.run_id)"
    Write-Host "Diff $($run.run_id): nodes=$($diff.counts.nodes) edges=$($diff.counts.edges)"
    $body = @{ reviewer_actor = $Reviewer } | ConvertTo-Json
    $approved = Invoke-RestMethod -Method Post -Uri "$ApiUrl/reviews/$($run.run_id)/approve" -ContentType "application/json" -Body $body
    Write-Host "Approved $($approved.run.run_id) by $($approved.run.reviewer_actor)"
}

Invoke-RestMethod -Method Get -Uri "$ApiUrl/entities/products"
Invoke-RestMethod -Method Post -Uri "$ApiUrl/agents/content" -ContentType "application/json" -Body (@{ topic = "reducing manufacturing inventory"; actor = "content-agent" } | ConvertTo-Json)
Invoke-RestMethod -Method Post -Uri "$ApiUrl/agents/gtm" -ContentType "application/json" -Body (@{ product = "Stockly"; actor = "gtm-agent" } | ConvertTo-Json)
