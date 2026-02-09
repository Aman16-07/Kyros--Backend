#!/usr/bin/env bash
# ============================================================
#  KYROS BACKEND – curl E2E Tests (Bash)
#  Covers: Auth, CRUD, Workflow, Phase 2 OTB Mgmt,
#          Phase 2 Range Architecture, Analytics, Lock
# ============================================================
set -euo pipefail
BASE="http://localhost:8000"
API="$BASE/api/v1"
TOKEN=""
PASS=0; FAIL=0
BODY="_curl_body.json"

NC='\033[0m'; GRN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; CYN='\033[0;36m'; MAG='\033[0;35m'; DIM='\033[0;90m'

write_body() { printf '%s' "$1" > "$BODY"; }

t() {
    local method="$1" url="$2" body="${3:-}" desc="${4:-}" expect="${5:-200}"
    local args=(-s -w '\n%{http_code}' -X "$method" -H 'Content-Type: application/json')
    [ -n "$TOKEN" ] && args+=(-H "Authorization: Bearer $TOKEN")
    if [ -n "$body" ]; then write_body "$body"; args+=(-d "@$BODY"); fi
    args+=("$url")
    local resp; resp=$(curl "${args[@]}" 2>/dev/null) || true
    local sc; sc=$(echo "$resp" | tail -1)
    local rb; rb=$(echo "$resp" | sed '$d')
    if [ "$sc" -eq "$expect" ] || { [ "$expect" -eq 200 ] && [ "$sc" -eq 201 ]; } || { [ "$expect" -eq 201 ] && [ "$sc" -eq 200 ]; }; then
        ((PASS++)) || true
        printf "  ${GRN}PASS [%s] %s${NC}\n" "$sc" "$desc" >&2
        echo "$rb"
    else
        ((FAIL++)) || true
        printf "  ${RED}FAIL [%s] %s (exp %s)${NC}\n" "$sc" "$desc" "$expect" >&2
        printf "  ${DIM}%.200s${NC}\n" "$rb" >&2
        echo ""
    fi
}

# helper: extract JSON field with python or jq
jval() {
    local pycmd="import sys,json; d=json.loads(sys.stdin.read()); print(d$1)"
    python3 -c "$pycmd" 2>/dev/null || python -c "$pycmd" 2>/dev/null || echo ""
}

printf "${CYN}======================================${NC}\n" >&2
printf "${CYN}  KYROS curl E2E TESTS  $(date '+%Y-%m-%d %H:%M')${NC}\n" >&2
printf "${CYN}======================================${NC}\n" >&2

# ── 1. HEALTH ──
printf "\n${YEL}[1] HEALTH${NC}\n" >&2
t GET "$BASE/"       "" "Root"
t GET "$BASE/health" "" "Health"
t GET "$BASE/ready"  "" "Ready"

# ── 2. AUTH ──
printf "\n${YEL}[2] AUTH${NC}\n" >&2
REG=$(t POST "$API/auth/register" '{"name":"Bash Admin","email":"bashadmin@test.com","password":"Bash1234Ab"}' "Register" 201)
TOKEN=$(echo "$REG" | jval '["tokens"]["access_token"]')
if [ -n "$TOKEN" ]; then printf "  ${CYN}token acquired (register)${NC}\n" >&2; fi

LGN=$(t POST "$API/auth/login" '{"email":"bashadmin@test.com","password":"Bash1234Ab"}' "Login")
TK2=$(echo "$LGN" | jval '["tokens"]["access_token"]')
if [ -n "$TK2" ]; then TOKEN="$TK2"; printf "  ${CYN}token acquired (login)${NC}\n" >&2; fi

t GET "$API/auth/me" "" "Me"

# ── 3. CLUSTERS ──
printf "\n${YEL}[3] CLUSTERS${NC}\n" >&2
CL=$(t POST "$API/clusters" '{"name":"South Region","description":"Southern stores"}' "Create cluster" 201)
CID=$(echo "$CL" | jval '["id"]')
t GET "$API/clusters" "" "List clusters"
[ -n "$CID" ] && t GET "$API/clusters/$CID" "" "Get cluster"

# ── 4. LOCATIONS ──
printf "\n${YEL}[4] LOCATIONS${NC}\n" >&2
LID=""
if [ -n "$CID" ]; then
    LOC=$(t POST "$API/locations" "{\"name\":\"Atlanta Store\",\"type\":\"store\",\"cluster_id\":\"$CID\",\"city\":\"Atlanta\",\"country\":\"USA\"}" "Create store" 201)
    LID=$(echo "$LOC" | jval '["id"]')
    t POST "$API/locations" "{\"name\":\"Memphis WH\",\"type\":\"warehouse\",\"cluster_id\":\"$CID\",\"city\":\"Memphis\",\"country\":\"USA\"}" "Create warehouse" 201
fi
t GET "$API/locations"            "" "List locations"
t GET "$API/locations/stores"     "" "List stores"
t GET "$API/locations/warehouses" "" "List warehouses"

# ── 5. CATEGORIES ──
printf "\n${YEL}[5] CATEGORIES${NC}\n" >&2
CAT=$(t POST "$API/categories" '{"name":"Accessories","code":"ACC","description":"Bags, hats, etc."}' "Create root category" 201)
CATID=$(echo "$CAT" | jval '["id"]')
SCID=""
if [ -n "$CATID" ]; then
    SC=$(t POST "$API/categories" "{\"name\":\"Bags\",\"code\":\"BAG\",\"description\":\"Handbags\",\"parent_id\":\"$CATID\"}" "Create child category" 201)
    SCID=$(echo "$SC" | jval '["id"]')
fi
t GET "$API/categories"      "" "List categories"
t GET "$API/categories/tree" "" "Category tree"

# ── 6. SEASONS ──
printf "\n${YEL}[6] SEASONS${NC}\n" >&2
SN=$(t POST "$API/seasons" '{"name":"Autumn 2026","start_date":"2026-09-01","end_date":"2026-11-30"}' "Create season" 201)
SID=$(echo "$SN" | jval '["id"]')
t GET "$API/seasons" "" "List seasons"

if [ -n "$SID" ]; then
    t GET "$API/seasons/$SID"                 "" "Get season"
    t GET "$API/seasons/$SID/workflow-status"  "" "Workflow status"

    printf "  ${MAG}-- Step 1: Define Locations --${NC}\n" >&2
    t POST "$API/seasons/$SID/define-locations" "{}" "Define locations"

    # ── 7. PLANS ──
    printf "\n${YEL}[7] PLANS${NC}\n" >&2
    if [ -n "$LID" ] && [ -n "$CATID" ]; then
        t POST "$API/plans" "{\"season_id\":\"$SID\",\"location_id\":\"$LID\",\"category_id\":\"$CATID\",\"planned_sales\":110000,\"planned_margin\":27,\"inventory_turns\":4.5}" "Create plan" 201
        t GET "$API/plans?season_id=$SID" "" "List plans"
    fi

    printf "  ${MAG}-- Step 2: Plan Upload --${NC}\n" >&2
    t POST "$API/seasons/$SID/complete-plan-upload" "{}" "Complete plan upload"

    # ── 8. OTB ──
    printf "\n${YEL}[8] OTB${NC}\n" >&2
    if [ -n "$LID" ] && [ -n "$CATID" ]; then
        t POST "$API/otb" "{\"season_id\":\"$SID\",\"location_id\":\"$LID\",\"category_id\":\"$CATID\",\"month\":\"2026-09-01\",\"planned_sales\":110000,\"planned_closing_stock\":55000,\"opening_stock\":32000,\"on_order\":11000,\"approved_spend_limit\":120000}" "Create OTB Sep" 201
        t POST "$API/otb" "{\"season_id\":\"$SID\",\"location_id\":\"$LID\",\"category_id\":\"$CATID\",\"month\":\"2026-10-01\",\"planned_sales\":85000,\"planned_closing_stock\":42000,\"opening_stock\":55000,\"on_order\":7000,\"approved_spend_limit\":70000}" "Create OTB Oct" 201
        t GET "$API/otb?season_id=$SID"         "" "List OTB"
        t GET "$API/otb/summary?season_id=$SID" "" "OTB summary"
    fi

    printf "  ${MAG}-- Step 3: OTB Upload --${NC}\n" >&2
    t POST "$API/seasons/$SID/complete-otb-upload" "{}" "Complete OTB upload"

    # ── 9. RANGE INTENT ──
    printf "\n${YEL}[9] RANGE INTENT${NC}\n" >&2
    if [ -n "$CATID" ]; then
        t POST "$API/range-intent" "{\"season_id\":\"$SID\",\"category_id\":\"$CATID\",\"core_percent\":50,\"fashion_percent\":50,\"price_band_mix\":{\"low\":30,\"mid\":40,\"high\":30}}" "Create range intent" 201
        t GET "$API/range-intent?season_id=$SID" "" "List range intents"
    fi

    printf "  ${MAG}-- Step 4: Range Upload --${NC}\n" >&2
    t POST "$API/seasons/$SID/complete-range-upload" "{}" "Complete range upload"

    # ── 10. PURCHASE ORDERS ──
    printf "\n${YEL}[10] PURCHASE ORDERS${NC}\n" >&2
    POID=""
    if [ -n "$LID" ] && [ -n "$CATID" ]; then
        PO=$(t POST "$API/purchase-orders" "{\"season_id\":\"$SID\",\"location_id\":\"$LID\",\"category_id\":\"$CATID\",\"po_number\":\"PO-BSH-001\",\"po_value\":28000,\"order_date\":\"2026-09-15\",\"supplier_name\":\"Trend Textiles\",\"source\":\"api\",\"status\":\"confirmed\"}" "Create PO 1" 201)
        POID=$(echo "$PO" | jval '["id"]')
        t POST "$API/purchase-orders" "{\"season_id\":\"$SID\",\"location_id\":\"$LID\",\"category_id\":\"$CATID\",\"po_number\":\"PO-BSH-002\",\"po_value\":16000,\"order_date\":\"2026-10-01\",\"supplier_name\":\"Classic Fabrics\",\"source\":\"api\",\"status\":\"shipped\"}" "Create PO 2" 201
        t GET "$API/purchase-orders?season_id=$SID"        "" "List POs"
        t GET "$API/purchase-orders/summary?season_id=$SID" "" "PO summary"
        t GET "$API/purchase-orders/by-number/PO-BSH-001"  "" "Get PO by number"
    fi

    # ── 11. GRN ──
    printf "\n${YEL}[11] GRN${NC}\n" >&2
    if [ -n "$POID" ]; then
        t POST "$API/grn" "{\"po_id\":\"$POID\",\"grn_date\":\"2026-10-10\",\"received_value\":22000}" "Create GRN" 201
        t GET "$API/grn?po_id=$POID"          "" "List GRN"
        t GET "$API/grn/fulfillment/$POID"     "" "Fulfillment"
    fi

    # ── 12. OTB MANAGEMENT ──
    printf "\n${YEL}[12] OTB MANAGEMENT${NC}\n" >&2
    t POST "$API/otb-management/$SID/recalculate" "{}" "Recalculate"
    t GET  "$API/otb-management/$SID/dashboard"   "" "Dashboard"
    t GET  "$API/otb-management/$SID/position"    "" "Position"
    t GET  "$API/otb-management/$SID/consumption" "" "Consumption"
    t GET  "$API/otb-management/$SID/forecast"    "" "Forecast"
    t GET  "$API/otb-management/$SID/alerts"      "" "Alerts"

    if [ -n "$CATID" ] && [ -n "$SCID" ]; then
        ADJ=$(t POST "$API/otb-management/$SID/adjust" "{\"season_id\":\"$SID\",\"from_category_id\":\"$CATID\",\"to_category_id\":\"$SCID\",\"amount\":5000,\"reason\":\"Budget shift\"}" "Create adjustment" 201)
        ADJID=$(echo "$ADJ" | jval '["id"]')
        t GET "$API/otb-management/$SID/adjustments" "" "List adjustments"
        [ -n "$ADJID" ] && t POST "$API/otb-management/adjustments/$ADJID/approve" "{}" "Approve adjustment"
    fi

    # ── 13. RANGE ARCHITECTURE ──
    printf "\n${YEL}[13] RANGE ARCHITECTURE${NC}\n" >&2
    RAID=""; RAID2=""
    if [ -n "$CATID" ]; then
        RA=$(t POST "$API/range/$SID/architecture" "{\"season_id\":\"$SID\",\"category_id\":\"$CATID\",\"price_band\":\"mid\",\"fabric\":\"cotton\",\"color_family\":\"blues\",\"style_type\":\"core\",\"planned_styles\":15,\"planned_options\":45,\"planned_depth\":200}" "Create range arch 1" 201)
        RAID=$(echo "$RA" | jval '["id"]')

        RA2=$(t POST "$API/range/$SID/architecture" "{\"season_id\":\"$SID\",\"category_id\":\"$CATID\",\"price_band\":\"high\",\"fabric\":\"silk\",\"color_family\":\"neutrals\",\"style_type\":\"fashion\",\"planned_styles\":8,\"planned_options\":24,\"planned_depth\":100}" "Create range arch 2" 201)
        RAID2=$(echo "$RA2" | jval '["id"]')

        t GET "$API/range/$SID/architecture" "" "List range arch"
        if [ -n "$RAID" ]; then
            t GET   "$API/range/$SID/architecture/$RAID" "" "Get range arch"
            t PATCH "$API/range/$SID/architecture/$RAID" '{"planned_styles":18}' "Update range arch"
        fi
        if [ -n "$RAID" ] && [ -n "$RAID2" ]; then
            t POST "$API/range/$SID/submit"  "{\"range_ids\":[\"$RAID\",\"$RAID2\"]}" "Submit ranges"
            t POST "$API/range/$SID/approve" "{\"range_ids\":[\"$RAID\",\"$RAID2\"],\"comment\":\"Approved\"}" "Approve ranges"
        fi
    fi

    SN2=$(t POST "$API/seasons" '{"name":"Spring 2025","start_date":"2025-03-01","end_date":"2025-05-31"}' "Create prior season" 201)
    SID2=$(echo "$SN2" | jval '["id"]')
    [ -n "$SID2" ] && t GET "$API/range/$SID/compare/$SID2" "" "Compare ranges"

    # ── 14. ANALYTICS ──
    printf "\n${YEL}[14] ANALYTICS${NC}\n" >&2
    t GET "$API/analytics/dashboard/$SID"          "" "Dashboard"
    t GET "$API/analytics/budget-vs-actual/$SID"   "" "Budget vs actual"
    t GET "$API/analytics/category-breakdown/$SID" "" "Category breakdown"
    t GET "$API/analytics/po-status/$SID"          "" "PO status"
    t GET "$API/analytics/workflow-status"          "" "All workflows"

    # ── 15. LOCK ──
    printf "\n${YEL}[15] LOCK SEASON${NC}\n" >&2
    t POST "$API/seasons/$SID/lock" "{}" "Lock season"
    t GET  "$API/analytics/read-only-view/$SID"  "" "Read-only view"
    t GET  "$API/seasons/$SID/workflow-status"    "" "Final workflow"
fi

# ── CLEANUP ──
rm -f "$BODY"

# ── RESULTS ──
printf "\n${CYN}======================================${NC}\n" >&2
printf "  ${GRN}Passed: %d${NC}\n" "$PASS" >&2
if [ "$FAIL" -gt 0 ]; then
    printf "  ${RED}Failed: %d${NC}\n" "$FAIL" >&2
else
    printf "  ${GRN}Failed: %d${NC}\n" "$FAIL" >&2
fi
printf "  Total:  %d\n" "$((PASS+FAIL))"
printf "${CYN}======================================${NC}\n" >&2
if [ "$FAIL" -eq 0 ]; then printf "  ${GRN}ALL TESTS PASSED!${NC}\n" >&2
else printf "  ${RED}SOME TESTS FAILED${NC}\n"; fi >&2
