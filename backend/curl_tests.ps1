#!/usr/bin/env pwsh
# ============================================================
#  KYROS BACKEND – curl E2E Tests (PowerShell)
#  Covers: Auth, CRUD, Workflow, Phase 2 OTB Management,
#          Phase 2 Range Architecture, Analytics, Lock
# ============================================================
$ErrorActionPreference = "Continue"
$BASE = "http://localhost:8000"
$API  = "$BASE/api/v1"
$TOKEN = ""
$PASS = 0; $FAIL = 0
$BODY = "_curl_body.json"

function Write-Body { param([string]$J); [IO.File]::WriteAllText($BODY,$J,[Text.Encoding]::UTF8) }

function T {
    param([string]$M,[string]$U,[string]$B,[string]$D,[int]$E=200)
    try {
        $a = @("-s","-w","`n%{http_code}","-X",$M,"-H","Content-Type: application/json")
        if ($script:TOKEN) { $a += @("-H","Authorization: Bearer $($script:TOKEN)") }
        if ($B) { Write-Body $B; $a += @("-d","@$BODY") }
        $a += $U
        $r = & curl.exe @a 2>$null
        $lines = $r -split "`n"
        $sc = [int]$lines[-1]
        $rb = ($lines[0..($lines.Length-2)] -join "`n")
        if ($sc -eq $E -or ($E -eq 200 -and $sc -eq 201) -or ($E -eq 201 -and $sc -eq 200)) {
            $script:PASS++; Write-Host "  PASS [$sc] $D" -Fore Green
            return ($rb | ConvertFrom-Json -EA SilentlyContinue)
        } else {
            $script:FAIL++; Write-Host "  FAIL [$sc] $D (exp $E)" -Fore Red
            Write-Host "       $($rb.Substring(0,[Math]::Min($rb.Length,200)))" -Fore DarkGray
            return $null
        }
    } catch { $script:FAIL++; Write-Host "  FAIL $D - $_" -Fore Red; return $null }
}

Write-Host "======================================" -Fore Cyan
Write-Host "  KYROS curl E2E TESTS  $(Get-Date -f 'yyyy-MM-dd HH:mm')" -Fore Cyan
Write-Host "======================================" -Fore Cyan

# ── 1. HEALTH ──
Write-Host "`n[1] HEALTH" -Fore Yellow
T -M GET -U "$BASE/"       -D "Root"
T -M GET -U "$BASE/health" -D "Health"
T -M GET -U "$BASE/ready"  -D "Ready"

# ── 2. AUTH ──
Write-Host "`n[2] AUTH" -Fore Yellow
$reg = T -M POST -U "$API/auth/register" -B '{"name":"Curl Admin","email":"curladmin@test.com","password":"Curl1234Ab"}' -D "Register" -E 201
if ($reg -and $reg.tokens) { $TOKEN = $reg.tokens.access_token; Write-Host "       token acquired (register)" -Fore DarkCyan }
$lgn = T -M POST -U "$API/auth/login" -B '{"email":"curladmin@test.com","password":"Curl1234Ab"}' -D "Login"
if ($lgn -and $lgn.tokens) { $TOKEN = $lgn.tokens.access_token; Write-Host "       token acquired (login)" -Fore DarkCyan }
T -M GET -U "$API/auth/me" -D "Me"

# ── 3. CLUSTERS ──
Write-Host "`n[3] CLUSTERS" -Fore Yellow
$cl = T -M POST -U "$API/clusters" -B '{"name":"West Region","description":"Western stores"}' -D "Create cluster" -E 201
$CID = if ($cl) { $cl.id } else { $null }
T -M GET -U "$API/clusters" -D "List clusters"
if ($CID) { T -M GET -U "$API/clusters/$CID" -D "Get cluster" }

# ── 4. LOCATIONS ──
Write-Host "`n[4] LOCATIONS" -Fore Yellow
$LID = $null
if ($CID) {
    $b = '{"name":"SF Store","type":"store","cluster_id":"'+$CID+'","city":"San Francisco","country":"USA"}'
    $loc = T -M POST -U "$API/locations" -B $b -D "Create store" -E 201
    $LID = if ($loc) { $loc.id } else { $null }
    $b2 = '{"name":"Oakland WH","type":"warehouse","cluster_id":"'+$CID+'","city":"Oakland","country":"USA"}'
    T -M POST -U "$API/locations" -B $b2 -D "Create warehouse" -E 201
}
T -M GET -U "$API/locations"            -D "List locations"
T -M GET -U "$API/locations/stores"     -D "List stores"
T -M GET -U "$API/locations/warehouses" -D "List warehouses"

# ── 5. CATEGORIES ──
Write-Host "`n[5] CATEGORIES" -Fore Yellow
$cat = T -M POST -U "$API/categories" -B '{"name":"Footwear","code":"FTW","description":"Shoes & boots"}' -D "Create root category" -E 201
$CATID = if ($cat) { $cat.id } else { $null }
$SCID = $null
if ($CATID) {
    $b = '{"name":"Sneakers","code":"SNK","description":"Athletic shoes","parent_id":"'+$CATID+'"}'
    $sc = T -M POST -U "$API/categories" -B $b -D "Create child category" -E 201
    $SCID = if ($sc) { $sc.id } else { $null }
}
T -M GET -U "$API/categories"      -D "List categories"
T -M GET -U "$API/categories/tree" -D "Category tree"

# ── 6. SEASONS + WORKFLOW ──
Write-Host "`n[6] SEASONS" -Fore Yellow
$sn = T -M POST -U "$API/seasons" -B '{"name":"Summer 2026","start_date":"2026-06-01","end_date":"2026-08-31"}' -D "Create season" -E 201
$SID = if ($sn) { $sn.id } else { $null }
T -M GET -U "$API/seasons" -D "List seasons"
if ($SID) {
    T -M GET -U "$API/seasons/$SID" -D "Get season"
    T -M GET -U "$API/seasons/$SID/workflow-status" -D "Workflow status"

    Write-Host "  -- Step 1: Define Locations --" -Fore Magenta
    T -M POST -U "$API/seasons/$SID/define-locations" -B "{}" -D "Define locations"

    # ── 7. PLANS ──
    Write-Host "`n[7] PLANS" -Fore Yellow
    if ($LID -and $CATID) {
        $b = '{"season_id":"'+$SID+'","location_id":"'+$LID+'","category_id":"'+$CATID+'","planned_sales":120000,"planned_margin":28,"inventory_turns":5}'
        T -M POST -U "$API/plans" -B $b -D "Create plan" -E 201
        T -M GET -U "$API/plans?season_id=$SID" -D "List plans"
    }

    Write-Host "  -- Step 2: Plan Upload --" -Fore Magenta
    T -M POST -U "$API/seasons/$SID/complete-plan-upload" -B "{}" -D "Complete plan upload"

    # ── 8. OTB (Phase 1 Static) ──
    Write-Host "`n[8] OTB" -Fore Yellow
    if ($LID -and $CATID) {
        $b1 = '{"season_id":"'+$SID+'","location_id":"'+$LID+'","category_id":"'+$CATID+'","month":"2026-06-01","planned_sales":120000,"planned_closing_stock":60000,"opening_stock":35000,"on_order":12000,"approved_spend_limit":130000}'
        T -M POST -U "$API/otb" -B $b1 -D "Create OTB Jun" -E 201
        $b2 = '{"season_id":"'+$SID+'","location_id":"'+$LID+'","category_id":"'+$CATID+'","month":"2026-07-01","planned_sales":90000,"planned_closing_stock":45000,"opening_stock":60000,"on_order":8000,"approved_spend_limit":75000}'
        T -M POST -U "$API/otb" -B $b2 -D "Create OTB Jul" -E 201
        T -M GET -U "$API/otb?season_id=$SID"         -D "List OTB"
        T -M GET -U "$API/otb/summary?season_id=$SID"  -D "OTB summary"
    }

    Write-Host "  -- Step 3: OTB Upload --" -Fore Magenta
    T -M POST -U "$API/seasons/$SID/complete-otb-upload" -B "{}" -D "Complete OTB upload"

    # ── 9. RANGE INTENT (Phase 1) ──
    Write-Host "`n[9] RANGE INTENT" -Fore Yellow
    if ($CATID) {
        $b = '{"season_id":"'+$SID+'","category_id":"'+$CATID+'","core_percent":55,"fashion_percent":45,"price_band_mix":{"low":25,"mid":50,"high":25}}'
        T -M POST -U "$API/range-intent" -B $b -D "Create range intent" -E 201
        T -M GET -U "$API/range-intent?season_id=$SID" -D "List range intents"
    }

    Write-Host "  -- Step 4: Range Upload --" -Fore Magenta
    T -M POST -U "$API/seasons/$SID/complete-range-upload" -B "{}" -D "Complete range upload"

    # ── 10. PURCHASE ORDERS ──
    Write-Host "`n[10] PURCHASE ORDERS" -Fore Yellow
    $POID = $null
    if ($LID -and $CATID) {
        $b1 = '{"season_id":"'+$SID+'","location_id":"'+$LID+'","category_id":"'+$CATID+'","po_number":"PO-CRL-001","po_value":30000,"order_date":"2026-06-15","supplier_name":"Style Corp","source":"api","status":"confirmed"}'
        $po = T -M POST -U "$API/purchase-orders" -B $b1 -D "Create PO 1" -E 201
        $POID = if ($po) { $po.id } else { $null }
        $b2 = '{"season_id":"'+$SID+'","location_id":"'+$LID+'","category_id":"'+$CATID+'","po_number":"PO-CRL-002","po_value":18000,"order_date":"2026-07-01","supplier_name":"Urban Threads","source":"api","status":"shipped"}'
        T -M POST -U "$API/purchase-orders" -B $b2 -D "Create PO 2" -E 201
        T -M GET -U "$API/purchase-orders?season_id=$SID"        -D "List POs"
        T -M GET -U "$API/purchase-orders/summary?season_id=$SID" -D "PO summary"
        T -M GET -U "$API/purchase-orders/by-number/PO-CRL-001"  -D "Get PO by number"
    }

    # ── 11. GRN ──
    Write-Host "`n[11] GRN" -Fore Yellow
    if ($POID) {
        $b = '{"po_id":"'+$POID+'","grn_date":"2026-07-10","received_value":25000}'
        T -M POST -U "$API/grn" -B $b -D "Create GRN" -E 201
        T -M GET -U "$API/grn?po_id=$POID"            -D "List GRN"
        T -M GET -U "$API/grn/fulfillment/$POID"       -D "Fulfillment"
    }

    # ── 12. PHASE 2: OTB MANAGEMENT ──
    Write-Host "`n[12] OTB MANAGEMENT" -Fore Yellow
    T -M POST -U "$API/otb-management/$SID/recalculate" -B "{}" -D "Recalculate"
    T -M GET  -U "$API/otb-management/$SID/dashboard"   -D "Dashboard"
    T -M GET  -U "$API/otb-management/$SID/position"    -D "Position"
    T -M GET  -U "$API/otb-management/$SID/consumption" -D "Consumption"
    T -M GET  -U "$API/otb-management/$SID/forecast"    -D "Forecast"
    T -M GET  -U "$API/otb-management/$SID/alerts"      -D "Alerts"

    if ($CATID -and $SCID) {
        $b = '{"season_id":"'+$SID+'","from_category_id":"'+$CATID+'","to_category_id":"'+$SCID+'","amount":5000,"reason":"Budget shift"}'
        $adj = T -M POST -U "$API/otb-management/$SID/adjust" -B $b -D "Create adjustment" -E 201
        $ADJID = if ($adj) { $adj.id } else { $null }
        T -M GET -U "$API/otb-management/$SID/adjustments" -D "List adjustments"
        if ($ADJID) { T -M POST -U "$API/otb-management/adjustments/$ADJID/approve" -B "{}" -D "Approve adjustment" }
    }

    # ── 13. PHASE 2: RANGE ARCHITECTURE ──
    Write-Host "`n[13] RANGE ARCHITECTURE" -Fore Yellow
    $RAID = $null; $RAID2 = $null
    if ($CATID) {
        $b1 = '{"season_id":"'+$SID+'","category_id":"'+$CATID+'","price_band":"mid","fabric":"cotton","color_family":"blues","style_type":"core","planned_styles":15,"planned_options":45,"planned_depth":200}'
        $ra = T -M POST -U "$API/range/$SID/architecture" -B $b1 -D "Create range arch 1" -E 201
        $RAID = if ($ra) { $ra.id } else { $null }

        $b2 = '{"season_id":"'+$SID+'","category_id":"'+$CATID+'","price_band":"high","fabric":"silk","color_family":"neutrals","style_type":"fashion","planned_styles":8,"planned_options":24,"planned_depth":100}'
        $ra2 = T -M POST -U "$API/range/$SID/architecture" -B $b2 -D "Create range arch 2" -E 201
        $RAID2 = if ($ra2) { $ra2.id } else { $null }

        T -M GET -U "$API/range/$SID/architecture" -D "List range arch"
        if ($RAID) {
            T -M GET   -U "$API/range/$SID/architecture/$RAID" -D "Get range arch"
            T -M PATCH -U "$API/range/$SID/architecture/$RAID" -B '{"planned_styles":18}' -D "Update range arch"
        }
        if ($RAID -and $RAID2) {
            $bs = '{"range_ids":["'+$RAID+'","'+$RAID2+'"]}'
            T -M POST -U "$API/range/$SID/submit"  -B $bs -D "Submit ranges"
            $ba = '{"range_ids":["'+$RAID+'","'+$RAID2+'"],"comment":"Looks good"}'
            T -M POST -U "$API/range/$SID/approve" -B $ba -D "Approve ranges"
        }
    }

    $sn2 = T -M POST -U "$API/seasons" -B '{"name":"Winter 2025","start_date":"2025-12-01","end_date":"2026-02-28"}' -D "Create prior season" -E 201
    $SID2 = if ($sn2) { $sn2.id } else { $null }
    if ($SID2) { T -M GET -U "$API/range/$SID/compare/$SID2" -D "Compare ranges" }

    # ── 14. ANALYTICS ──
    Write-Host "`n[14] ANALYTICS" -Fore Yellow
    T -M GET -U "$API/analytics/dashboard/$SID"          -D "Dashboard"
    T -M GET -U "$API/analytics/budget-vs-actual/$SID"   -D "Budget vs actual"
    T -M GET -U "$API/analytics/category-breakdown/$SID" -D "Category breakdown"
    T -M GET -U "$API/analytics/po-status/$SID"          -D "PO status"
    T -M GET -U "$API/analytics/workflow-status"          -D "All workflows"

    # ── 15. LOCK ──
    Write-Host "`n[15] LOCK SEASON" -Fore Yellow
    T -M POST -U "$API/seasons/$SID/lock" -B "{}" -D "Lock season"
    T -M GET  -U "$API/analytics/read-only-view/$SID"   -D "Read-only view"
    T -M GET  -U "$API/seasons/$SID/workflow-status"     -D "Final workflow"
}

# ── CLEANUP ──
Remove-Item -Force $BODY -EA SilentlyContinue

# ── RESULTS ──
Write-Host "`n======================================" -Fore Cyan
Write-Host "  Passed: $PASS" -Fore Green
Write-Host "  Failed: $FAIL" -Fore $(if ($FAIL -gt 0){"Red"}else{"Green"})
Write-Host "  Total:  $($PASS+$FAIL)" -Fore White
Write-Host "======================================" -Fore Cyan
if ($FAIL -eq 0) { Write-Host "  ALL TESTS PASSED!" -Fore Green }
else              { Write-Host "  SOME TESTS FAILED" -Fore Red }
