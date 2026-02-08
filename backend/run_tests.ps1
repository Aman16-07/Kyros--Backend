$ErrorActionPreference = "Continue"
$BASE = "http://localhost:8000"
$API = "$BASE/api/v1"
$PASS = 0
$FAIL = 0
$TOKEN = ""
$TMPFILE = "e:\Kyros\Kyros\backend\_test_body.json"

function Write-Body {
    param([string]$Json)
    [System.IO.File]::WriteAllText($TMPFILE, $Json, [System.Text.Encoding]::UTF8)
}

function Test-EP {
    param([string]$M, [string]$U, [string]$B, [string]$D, [int]$E = 200)
    try {
        $args_list = @("-s", "-w", "`n%{http_code}", "-X", $M)
        $args_list += @("-H", "Content-Type: application/json")
        if ($script:TOKEN) { $args_list += @("-H", "Authorization: Bearer $($script:TOKEN)") }
        if ($B) {
            Write-Body $B
            $args_list += @("-d", "@$TMPFILE")
        }
        $args_list += $U
        $r = & curl.exe @args_list 2>$null
        $lines = $r -split "`n"
        $sc = [int]$lines[-1]
        $rb = ($lines[0..($lines.Length-2)] -join "`n")
        if ($sc -eq $E -or ($E -eq 200 -and $sc -eq 201) -or ($E -eq 201 -and $sc -eq 200)) {
            $script:PASS++
            Write-Host "  PASS [$sc] $M $D" -ForegroundColor Green
            return ($rb | ConvertFrom-Json -ErrorAction SilentlyContinue)
        } else {
            $script:FAIL++
            Write-Host "  FAIL [$sc] $M $D (expected $E)" -ForegroundColor Red
            $short = if ($rb.Length -gt 200) { $rb.Substring(0,200) + "..." } else { $rb }
            Write-Host "       $short" -ForegroundColor DarkGray
            return $null
        }
    } catch {
        $script:FAIL++
        Write-Host "  FAIL $M $D - $_" -ForegroundColor Red
        return $null
    }
}

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  KYROS BACKEND - END-TO-END API TESTS" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. HEALTH
Write-Host ""
Write-Host "[1] HEALTH CHECKS" -ForegroundColor Yellow
Test-EP -M GET -U "$BASE/" -D "Root endpoint"
Test-EP -M GET -U "$BASE/health" -D "Health check"
Test-EP -M GET -U "$BASE/ready" -D "Ready check"

# 2. AUTH
Write-Host ""
Write-Host "[2] AUTHENTICATION" -ForegroundColor Yellow
$reg = Test-EP -M POST -U "$API/auth/register" -B '{"name":"Test Admin","email":"admin@testretail.com","password":"Test1234Ab"}' -D "Register user" -E 201
if ($reg -and $reg.tokens -and $reg.tokens.access_token) {
    $TOKEN = $reg.tokens.access_token
    Write-Host "       Token acquired from registration" -ForegroundColor DarkCyan
}

$login = Test-EP -M POST -U "$API/auth/login" -B '{"email":"admin@testretail.com","password":"Test1234Ab"}' -D "Login"
if ($login -and $login.tokens -and $login.tokens.access_token) {
    $TOKEN = $login.tokens.access_token
    Write-Host "       Token acquired from login" -ForegroundColor DarkCyan
}

Test-EP -M GET -U "$API/auth/me" -D "Get current user"

# 3. CLUSTERS
Write-Host ""
Write-Host "[3] CLUSTERS" -ForegroundColor Yellow
$cl = Test-EP -M POST -U "$API/clusters" -B '{"name":"Northeast Region","description":"NE US stores"}' -D "Create cluster" -E 201
$CID = if ($cl) { $cl.id } else { $null }
Test-EP -M GET -U "$API/clusters" -D "List clusters"
if ($CID) { Test-EP -M GET -U "$API/clusters/$CID" -D "Get cluster by ID" }

# 4. LOCATIONS
Write-Host ""
Write-Host "[4] LOCATIONS" -ForegroundColor Yellow
$LID = $null
if ($CID) {
    $body_store = '{"name":"Downtown NYC Store","type":"store","cluster_id":"' + $CID + '","city":"New York","country":"USA"}'
    $loc = Test-EP -M POST -U "$API/locations" -B $body_store -D "Create store" -E 201
    $LID = if ($loc) { $loc.id } else { $null }
    $body_wh = '{"name":"Central Warehouse","type":"warehouse","cluster_id":"' + $CID + '","city":"Newark","country":"USA"}'
    Test-EP -M POST -U "$API/locations" -B $body_wh -D "Create warehouse" -E 201
}
Test-EP -M GET -U "$API/locations" -D "List locations"
Test-EP -M GET -U "$API/locations/stores" -D "List stores"
Test-EP -M GET -U "$API/locations/warehouses" -D "List warehouses"

# 5. CATEGORIES
Write-Host ""
Write-Host "[5] CATEGORIES" -ForegroundColor Yellow
$cat = Test-EP -M POST -U "$API/categories" -B '{"name":"Apparel","code":"APP","description":"Clothing"}' -D "Create root category" -E 201
$CATID = if ($cat) { $cat.id } else { $null }
$SCID = $null
if ($CATID) {
    $body_sc = '{"name":"Menswear","code":"MEN","description":"Mens clothing","parent_id":"' + $CATID + '"}'
    $subcat = Test-EP -M POST -U "$API/categories" -B $body_sc -D "Create child category" -E 201
    $SCID = if ($subcat) { $subcat.id } else { $null }
}
Test-EP -M GET -U "$API/categories" -D "List categories"
Test-EP -M GET -U "$API/categories/tree" -D "Get category tree"

# 6. SEASONS
Write-Host ""
Write-Host "[6] SEASONS + WORKFLOW" -ForegroundColor Yellow
$sn = Test-EP -M POST -U "$API/seasons" -B '{"name":"Spring 2026","start_date":"2026-03-01","end_date":"2026-05-31"}' -D "Create season" -E 201
$SID = if ($sn) { $sn.id } else { $null }
Test-EP -M GET -U "$API/seasons" -D "List seasons"

if ($SID) {
    Test-EP -M GET -U "$API/seasons/$SID" -D "Get season"
    Test-EP -M GET -U "$API/seasons/$SID/workflow-status" -D "Workflow status"

    Write-Host "  -- Step 1: Define Locations --" -ForegroundColor Magenta
    Test-EP -M POST -U "$API/seasons/$SID/define-locations" -B "{}" -D "Define locations"

    # 7. PLANS
    Write-Host ""
    Write-Host "[7] SEASON PLANS" -ForegroundColor Yellow
    if ($LID -and $CATID) {
        $body_plan = '{"season_id":"' + $SID + '","location_id":"' + $LID + '","category_id":"' + $CATID + '","planned_sales":100000.00,"planned_margin":25.50,"inventory_turns":4.00}'
        Test-EP -M POST -U "$API/plans" -B $body_plan -D "Create plan" -E 201
        Test-EP -M GET -U "$API/plans?season_id=$SID" -D "List plans"
    }

    Write-Host "  -- Step 2: Plan Upload --" -ForegroundColor Magenta
    Test-EP -M POST -U "$API/seasons/$SID/complete-plan-upload" -B "{}" -D "Complete plan upload"

    # 8. OTB
    Write-Host ""
    Write-Host "[8] OTB PLANS (Phase 1 Static)" -ForegroundColor Yellow
    if ($LID -and $CATID) {
        $body_otb1 = '{"season_id":"' + $SID + '","location_id":"' + $LID + '","category_id":"' + $CATID + '","month":"2026-03-01","planned_sales":100000,"planned_closing_stock":50000,"opening_stock":30000,"on_order":10000,"approved_spend_limit":110000}'
        Test-EP -M POST -U "$API/otb" -B $body_otb1 -D "Create OTB Mar" -E 201
        $body_otb2 = '{"season_id":"' + $SID + '","location_id":"' + $LID + '","category_id":"' + $CATID + '","month":"2026-04-01","planned_sales":80000,"planned_closing_stock":40000,"opening_stock":50000,"on_order":5000,"approved_spend_limit":65000}'
        Test-EP -M POST -U "$API/otb" -B $body_otb2 -D "Create OTB Apr" -E 201
        Test-EP -M GET -U "$API/otb?season_id=$SID" -D "List OTB plans"
        Test-EP -M GET -U "$API/otb/summary?season_id=$SID" -D "OTB summary"
    }

    Write-Host "  -- Step 3: OTB Upload --" -ForegroundColor Magenta
    Test-EP -M POST -U "$API/seasons/$SID/complete-otb-upload" -B "{}" -D "Complete OTB upload"

    # 9. RANGE INTENT
    Write-Host ""
    Write-Host "[9] RANGE INTENT (Phase 1)" -ForegroundColor Yellow
    if ($CATID) {
        $body_ri = '{"season_id":"' + $SID + '","category_id":"' + $CATID + '","core_percent":60.00,"fashion_percent":40.00,"price_band_mix":{"low":30,"mid":50,"high":20}}'
        Test-EP -M POST -U "$API/range-intent" -B $body_ri -D "Create range intent" -E 201
        Test-EP -M GET -U "$API/range-intent?season_id=$SID" -D "List range intents"
    }

    Write-Host "  -- Step 4: Range Upload --" -ForegroundColor Magenta
    Test-EP -M POST -U "$API/seasons/$SID/complete-range-upload" -B "{}" -D "Complete range upload"

    # 10. PURCHASE ORDERS
    Write-Host ""
    Write-Host "[10] PURCHASE ORDERS" -ForegroundColor Yellow
    $POID = $null
    if ($LID -and $CATID) {
        $body_po1 = '{"season_id":"' + $SID + '","location_id":"' + $LID + '","category_id":"' + $CATID + '","po_number":"PO-2026-001","po_value":25000,"order_date":"2026-03-15","supplier_name":"Fashion Textiles","source":"api","status":"confirmed"}'
        $po = Test-EP -M POST -U "$API/purchase-orders" -B $body_po1 -D "Create PO 1" -E 201
        $POID = if ($po) { $po.id } else { $null }
        $body_po2 = '{"season_id":"' + $SID + '","location_id":"' + $LID + '","category_id":"' + $CATID + '","po_number":"PO-2026-002","po_value":15000,"order_date":"2026-04-01","supplier_name":"Premium Fabrics","source":"api","status":"shipped"}'
        Test-EP -M POST -U "$API/purchase-orders" -B $body_po2 -D "Create PO 2" -E 201
        Test-EP -M GET -U "$API/purchase-orders?season_id=$SID" -D "List POs"
        Test-EP -M GET -U "$API/purchase-orders/summary?season_id=$SID" -D "PO summary"
        Test-EP -M GET -U "$API/purchase-orders/by-number/PO-2026-001" -D "Get PO by number"
    }

    # 11. GRN
    Write-Host ""
    Write-Host "[11] GRN" -ForegroundColor Yellow
    if ($POID) {
        $body_grn = '{"po_id":"' + $POID + '","grn_date":"2026-04-10","received_value":20000}'
        Test-EP -M POST -U "$API/grn" -B $body_grn -D "Create GRN" -E 201
        Test-EP -M GET -U "$API/grn?po_id=$POID" -D "List GRN by PO"
        Test-EP -M GET -U "$API/grn/fulfillment/$POID" -D "Fulfillment status"
    }

    # 12. PHASE 2: OTB MANAGEMENT
    Write-Host ""
    Write-Host "[12] PHASE 2: OTB MANAGEMENT" -ForegroundColor Yellow
    Test-EP -M POST -U "$API/otb-management/$SID/recalculate" -B "{}" -D "Recalculate OTB"
    Test-EP -M GET -U "$API/otb-management/$SID/dashboard" -D "OTB Dashboard"
    Test-EP -M GET -U "$API/otb-management/$SID/position" -D "OTB Position"
    Test-EP -M GET -U "$API/otb-management/$SID/consumption" -D "OTB Consumption"
    Test-EP -M GET -U "$API/otb-management/$SID/forecast" -D "OTB Forecast"
    Test-EP -M GET -U "$API/otb-management/$SID/alerts" -D "OTB Alerts"

    if ($CATID -and $SCID) {
        $body_adj = '{"season_id":"' + $SID + '","from_category_id":"' + $CATID + '","to_category_id":"' + $SCID + '","amount":5000,"reason":"Rebalancing from Apparel to Menswear"}'
        $adj = Test-EP -M POST -U "$API/otb-management/$SID/adjust" -B $body_adj -D "Create adjustment" -E 201
        $ADJID = if ($adj) { $adj.id } else { $null }
        Test-EP -M GET -U "$API/otb-management/$SID/adjustments" -D "List adjustments"
        if ($ADJID) {
            Test-EP -M POST -U "$API/otb-management/adjustments/$ADJID/approve" -B "{}" -D "Approve adjustment"
        }
    }

    # 13. PHASE 2: RANGE ARCHITECTURE
    Write-Host ""
    Write-Host "[13] PHASE 2: RANGE ARCHITECTURE" -ForegroundColor Yellow
    $RAID = $null
    $RAID2 = $null
    if ($CATID) {
        $body_ra1 = '{"season_id":"' + $SID + '","category_id":"' + $CATID + '","price_band":"mid","fabric":"cotton","color_family":"blues","style_type":"core","planned_styles":15,"planned_options":45,"planned_depth":200}'
        $ra = Test-EP -M POST -U "$API/range/$SID/architecture" -B $body_ra1 -D "Create range arch 1" -E 201
        $RAID = if ($ra) { $ra.id } else { $null }

        $body_ra2 = '{"season_id":"' + $SID + '","category_id":"' + $CATID + '","price_band":"high","fabric":"silk","color_family":"neutrals","style_type":"fashion","planned_styles":8,"planned_options":24,"planned_depth":100}'
        $ra2 = Test-EP -M POST -U "$API/range/$SID/architecture" -B $body_ra2 -D "Create range arch 2" -E 201
        $RAID2 = if ($ra2) { $ra2.id } else { $null }

        Test-EP -M GET -U "$API/range/$SID/architecture" -D "List range architectures"

        if ($RAID) {
            Test-EP -M GET -U "$API/range/$SID/architecture/$RAID" -D "Get range by ID"
            Test-EP -M PATCH -U "$API/range/$SID/architecture/$RAID" -B '{"planned_styles":18}' -D "Update range arch"
        }

        if ($RAID -and $RAID2) {
            $body_submit = '{"range_ids":["' + $RAID + '","' + $RAID2 + '"]}'
            Test-EP -M POST -U "$API/range/$SID/submit" -B $body_submit -D "Submit for approval"
            $body_approve = '{"range_ids":["' + $RAID + '","' + $RAID2 + '"],"comment":"Approved"}'
            Test-EP -M POST -U "$API/range/$SID/approve" -B $body_approve -D "Approve ranges"
        }
    }

    $sn2 = Test-EP -M POST -U "$API/seasons" -B '{"name":"Fall 2025","start_date":"2025-09-01","end_date":"2025-11-30"}' -D "Create prior season" -E 201
    $SID2 = if ($sn2) { $sn2.id } else { $null }
    if ($SID2) {
        Test-EP -M GET -U "$API/range/$SID/compare/$SID2" -D "Compare ranges"
    }

    # 14. ANALYTICS
    Write-Host ""
    Write-Host "[14] ANALYTICS" -ForegroundColor Yellow
    Test-EP -M GET -U "$API/analytics/dashboard/$SID" -D "Dashboard"
    Test-EP -M GET -U "$API/analytics/budget-vs-actual/$SID" -D "Budget vs actual"
    Test-EP -M GET -U "$API/analytics/category-breakdown/$SID" -D "Category breakdown"
    Test-EP -M GET -U "$API/analytics/po-status/$SID" -D "PO status"
    Test-EP -M GET -U "$API/analytics/workflow-status" -D "All workflows"

    Write-Host "  -- Step 5: Lock Season --" -ForegroundColor Magenta
    Test-EP -M POST -U "$API/seasons/$SID/lock" -B "{}" -D "Lock season"
    Test-EP -M GET -U "$API/analytics/read-only-view/$SID" -D "Read-only view"
    Test-EP -M GET -U "$API/seasons/$SID/workflow-status" -D "Final workflow"
}

# CLEANUP
Remove-Item -Force $TMPFILE -ErrorAction SilentlyContinue

# RESULTS
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  TEST RESULTS" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  Passed: $PASS" -ForegroundColor Green
Write-Host "  Failed: $FAIL" -ForegroundColor $(if ($FAIL -gt 0) { "Red" } else { "Green" })
Write-Host "  Total:  $($PASS + $FAIL)" -ForegroundColor White
Write-Host "====================================================" -ForegroundColor Cyan
if ($FAIL -eq 0) { Write-Host "  ALL TESTS PASSED!" -ForegroundColor Green }
else { Write-Host "  SOME TESTS FAILED" -ForegroundColor Red }
