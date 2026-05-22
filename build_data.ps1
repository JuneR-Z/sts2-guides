# Build cards and relics data from spire-archive API
$ErrorActionPreference = "Stop"
$base = "https://spire-archive.com/api/sts2"

# Fetch all cards
Write-Host "Fetching cards..." -ForegroundColor Cyan
$allCards = @()
$offset = 0
do {
    $url = "$base/cards?lang=en&limit=300&offset=$offset"
    Write-Host "  Requesting offset=$offset..."
    $resp = Invoke-RestMethod -Uri $url -TimeoutSec 60
    $allCards += $resp.items
    $offset += $resp.limit
    Write-Host "  Got $($resp.items.Count) cards (total: $($allCards.Count))"
} while ($allCards.Count -lt $resp.total)

Write-Host "Total cards fetched: $($allCards.Count)" -ForegroundColor Green

# Fetch all relics
Write-Host "Fetching relics..." -ForegroundColor Cyan
$relicsResp = Invoke-RestMethod -Uri "$base/relics?lang=en&limit=300" -TimeoutSec 60
$allRelics = $relicsResp.items
Write-Host "Total relics fetched: $($allRelics.Count)" -ForegroundColor Green

# Auto-assign tier based on rarity
function Get-AutoTier($rarity) {
    switch ($rarity) {
        "Basic" { return "D" }
        "Common" { return "C" }
        "Uncommon" { return "B" }
        "Rare" { return "A" }
        "Ancient" { return "S" }
        "Event" { return "B" }
        "Curse" { return "D" }
        "Status" { return "D" }
        "Token" { return "C" }
        "Quest" { return "C" }
        default { return "C" }
    }
}

function Get-UpgradeText($card) {
    $upgrade = $card.upgrade
    if (-not $upgrade) { return "" }
    if ($upgrade -is [string]) { return "" }
    $props = $upgrade | Get-Member -MemberType NoteProperty
    if ($props.Count -eq 0) { return "" }
    
    # If upgrade has description, use it
    if ($upgrade.PSObject.Properties.Name -contains "description") {
        $desc = $upgrade.description
        if ($desc) { return $desc }
    }
    return ""
}

function Format-Cost($cost) {
    if ($null -eq $cost) { return "N/A" }
    if ($cost -is [int] -or $cost -is [long]) {
        return [string]$cost
    }
    return [string]$cost
}

$colorMap = @{
    "ironclad" = "ironclad"
    "silent" = "silent"
    "defect" = "defect"
    "necrobinder" = "necrobinder"
    "regent" = "regent"
}

# Transform cards
Write-Host "Transforming cards..." -ForegroundColor Cyan
$transformedCards = [System.Collections.ArrayList]::new()
foreach ($c in $allCards) {
    $char = $colorMap[$c.color]
    if (-not $char) { continue }
    
    # Skip duplicates for basic strike/defend (keep one per character from API)
    $rarity = if ($c.rarity) { 
        $r = $c.rarity.ToLower()
        (Get-Culture).TextInfo.ToTitleCase($r)
    } else { "Token" }
    
    $cardId = "$($char)_$($c.id.ToLower())"
    
    $desc = $c.description
    if ($desc) {
        $desc = $desc -replace '\n', ' '
        $desc = $desc -replace '\s+', ' '
        $desc = $desc.Trim()
    } else {
        $desc = ""
    }
    
    # Clean up template syntax artifacts
    $desc = $desc -replace '\{energyPrefix:energyIcons\(1\)\}', '[E]'
    $desc = $desc -replace '\{singleStarIcon\}', '[S]'
    $desc = $desc -replace '\{[^}]+\}', ''
    $desc = $desc -replace '\s+', ' '
    $desc = $desc.Trim()
    
    $upgradeDesc = Get-UpgradeText $c
    if ($upgradeDesc) {
        $upgradeDesc = $upgradeDesc -replace '\n', ' '
        $upgradeDesc = $upgradeDesc -replace '\{energyPrefix:energyIcons\(1\)\}', '[E]'
        $upgradeDesc = $upgradeDesc -replace '\{singleStarIcon\}', '[S]'
        $upgradeDesc = $upgradeDesc -replace '\{[^}]+\}', ''
    }
    
    $tier = Get-AutoTier $rarity
    
    $cardObj = [PSCustomObject]@{
        id = $cardId
        name = $c.name
        character = $char
        type = $c.type
        rarity = $rarity
        cost = $c.cost
        tier = $tier
        effect = $desc
        upgrade = $upgradeDesc
    }
    [void]$transformedCards.Add($cardObj)
}
Write-Host "  Transformed $($transformedCards.Count) cards"

# Transform relics
Write-Host "Transforming relics..." -ForegroundColor Cyan
$transformedRelics = [System.Collections.ArrayList]::new()
foreach ($r in $allRelics) {
    $outTier = switch ($r.tier) {
        "Starter" { "Starter" }
        "Common" { "C" }
        "Uncommon" { "B" }
        "Rare" { "A" }
        "Ancient" { "S" }
        "Shop" { "A" }
        "Event" { "B" }
        "None" { "D" }
        default { "C" }
    }
    
    $apiColor = $r.color
    $outChar = switch ($apiColor) {
        "ironclad" { "ironclad" }
        "silent" { "silent" }
        "defect" { "defect" }
        "necrobinder" { "necrobinder" }
        "regent" { "regent" }
        default { "all" }
    }
    
    $desc = $r.description
    if ($desc) {
        $desc = $desc -replace '\{[^}]+\}', ''
        $desc = $desc.Trim()
    }
    
    $relicObj = [PSCustomObject]@{
        id = $r.id.ToLower()
        name = $r.name
        tier = $outTier
        character = $outChar
        effect = $desc
        comment = ""
    }
    [void]$transformedRelics.Add($relicObj)
}
Write-Host "  Transformed $($transformedRelics.Count) relics"

# Build JSON outputs
Write-Host "Writing data files..." -ForegroundColor Cyan

# Cards data
$cardsJson = $transformedCards | ConvertTo-Json -Depth 4 -Compress
$cardsJs = "const cardsData = $cardsJson;"
$cardsPath = Join-Path $PSScriptRoot "en\cards\cards-data.js"
[System.IO.File]::WriteAllText($cardsPath, $cardsJs, [System.Text.Encoding]::UTF8)
Write-Host "  Written: en/cards/cards-data.js ($($transformedCards.Count) cards)"

# Relics data
$relicsJson = $transformedRelics | ConvertTo-Json -Depth 4 -Compress
$relicsJs = "const relicsData = $relicsJson;"
$relicsPath = Join-Path $PSScriptRoot "en\relics\relics-data.js"
[System.IO.File]::WriteAllText($relicsPath, $relicsJs, [System.Text.Encoding]::UTF8)
Write-Host "  Written: en/relics/relics-data.js ($($transformedRelics.Count) relics)"

Write-Host "Done!" -ForegroundColor Green
