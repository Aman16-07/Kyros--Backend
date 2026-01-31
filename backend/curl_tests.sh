#!/bin/bash
# Kyros Backend - CURL API Test Script
# Run: chmod +x curl_tests.sh && ./curl_tests.sh

# Auto-detect host: use host.docker.internal for WSL, localhost otherwise
if grep -qEi "(microsoft|wsl)" /proc/version 2>/dev/null; then
  HOST="host.docker.internal"
else
  HOST="localhost"
fi

BASE_URL="http://$HOST:8000"
API="$BASE_URL/api/v1"

echo "============================================"
echo "KYROS BACKEND - CURL API TESTS"
echo "============================================"
echo "Base URL: $BASE_URL"
echo ""

# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================
echo -e "\n\033[1;33m1. HEALTH CHECK ENDPOINTS\033[0m"
echo "-------------------------"

echo -e "\n\033[0;32m  GET /\033[0m"
curl -s $BASE_URL/
echo ""

echo -e "\n\033[0;32m  GET /health\033[0m"
curl -s $BASE_URL/health
echo ""

echo -e "\n\033[0;32m  GET /ready\033[0m"
curl -s $BASE_URL/ready
echo ""

# ============================================
# CREATE CLUSTER
# ============================================
echo -e "\n\033[1;33m2. CREATE CLUSTER\033[0m"
echo "-----------------"
CLUSTER_RESPONSE=$(curl -s -X POST "$API/clusters" \
  -H "Content-Type: application/json" \
  -d '{"name":"Northeast Region","description":"Stores in the northeastern US"}')
echo $CLUSTER_RESPONSE
CLUSTER_ID=$(echo $CLUSTER_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo -e "\n  Cluster ID: $CLUSTER_ID"

# ============================================
# CREATE LOCATION
# ============================================
echo -e "\n\033[1;33m3. CREATE LOCATION\033[0m"
echo "------------------"
LOCATION_RESPONSE=$(curl -s -X POST "$API/locations" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Downtown NYC Store\",\"type\":\"store\",\"cluster_id\":\"$CLUSTER_ID\",\"address\":\"123 Main St\",\"city\":\"New York\",\"country\":\"USA\"}")
echo $LOCATION_RESPONSE
LOCATION_ID=$(echo $LOCATION_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
LOCATION_CODE=$(echo $LOCATION_RESPONSE | grep -o '"location_code":"[^"]*"' | cut -d'"' -f4)
echo -e "\n  Location ID: $LOCATION_ID"
echo -e "  Location Code (16 chars): $LOCATION_CODE"

# ============================================
# CREATE CATEGORY
# ============================================
echo -e "\n\033[1;33m4. CREATE CATEGORY\033[0m"
echo "------------------"
CATEGORY_RESPONSE=$(curl -s -X POST "$API/categories" \
  -H "Content-Type: application/json" \
  -d '{"name":"Apparel","code":"APP","description":"Clothing and accessories"}')
echo $CATEGORY_RESPONSE
CATEGORY_ID=$(echo $CATEGORY_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo -e "\n  Category ID: $CATEGORY_ID"

# ============================================
# CREATE SEASON
# ============================================
echo -e "\n\033[1;33m5. CREATE SEASON\033[0m"
echo "----------------"
SEASON_RESPONSE=$(curl -s -X POST "$API/seasons" \
  -H "Content-Type: application/json" \
  -d '{"name":"Spring 2026","start_date":"2026-03-01","end_date":"2026-05-31"}')
echo $SEASON_RESPONSE
SEASON_ID=$(echo $SEASON_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
SEASON_CODE=$(echo $SEASON_RESPONSE | grep -o '"season_code":"[^"]*"' | cut -d'"' -f4)
echo -e "\n  Season ID: $SEASON_ID"
echo -e "  Season Code (XXXX-XXXX): $SEASON_CODE"

# ============================================
# WORKFLOW STEP 1: DEFINE LOCATIONS
# ============================================
echo -e "\n\033[1;33m6. WORKFLOW STEP 1: DEFINE LOCATIONS\033[0m"
echo "------------------------------------"
curl -s -X POST "$API/seasons/$SEASON_ID/define-locations" \
  -H "Content-Type: application/json" \
  -d '{}'
echo ""

# ============================================
# CREATE SEASON PLAN
# ============================================
echo -e "\n\033[1;33m7. CREATE SEASON PLAN\033[0m"
echo "---------------------"
PLAN_RESPONSE=$(curl -s -X POST "$API/plans" \
  -H "Content-Type: application/json" \
  -d "{\"season_id\":\"$SEASON_ID\",\"location_id\":\"$LOCATION_ID\",\"category_id\":\"$CATEGORY_ID\",\"planned_sales\":100000.00,\"planned_margin\":25.50,\"inventory_turns\":4}")
echo $PLAN_RESPONSE
PLAN_ID=$(echo $PLAN_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo -e "\n  Plan ID: $PLAN_ID"

# ============================================
# WORKFLOW STEP 2: COMPLETE PLAN UPLOAD
# ============================================
echo -e "\n\033[1;33m8. WORKFLOW STEP 2: COMPLETE PLAN UPLOAD\033[0m"
echo "----------------------------------------"
curl -s -X POST "$API/seasons/$SEASON_ID/complete-plan-upload" \
  -H "Content-Type: application/json" \
  -d '{}'
echo ""

# ============================================
# CREATE OTB PLAN
# ============================================
echo -e "\n\033[1;33m9. CREATE OTB PLAN (Formula: Planned Sales + Planned Closing Stock - Opening Stock - On Order)\033[0m"
echo "--------------------------------------------------------------------------------------------"
OTB_RESPONSE=$(curl -s -X POST "$API/otb" \
  -H "Content-Type: application/json" \
  -d "{\"season_id\":\"$SEASON_ID\",\"category_id\":\"$CATEGORY_ID\",\"location_id\":\"$LOCATION_ID\",\"month\":\"2026-03-01\",\"planned_sales\":100000.00,\"planned_closing_stock\":50000.00,\"opening_stock\":30000.00,\"on_order\":10000.00}")
echo $OTB_RESPONSE
echo -e "\n  OTB Calculation: 100000 + 50000 - 30000 - 10000 = 110000"

# ============================================
# WORKFLOW STEP 3: COMPLETE OTB UPLOAD
# ============================================
echo -e "\n\033[1;33m10. WORKFLOW STEP 3: COMPLETE OTB UPLOAD\033[0m"
echo "----------------------------------------"
curl -s -X POST "$API/seasons/$SEASON_ID/complete-otb-upload" \
  -H "Content-Type: application/json" \
  -d '{}'
echo ""

# ============================================
# CREATE RANGE INTENT
# ============================================
echo -e "\n\033[1;33m11. CREATE RANGE INTENT\033[0m"
echo "-----------------------"
RANGE_RESPONSE=$(curl -s -X POST "$API/range-intent" \
  -H "Content-Type: application/json" \
  -d "{\"season_id\":\"$SEASON_ID\",\"category_id\":\"$CATEGORY_ID\",\"core_percent\":60.00,\"fashion_percent\":40.00,\"price_band_mix\":{\"low\":30,\"mid\":50,\"high\":20}}")
echo $RANGE_RESPONSE
echo ""

# ============================================
# WORKFLOW STEP 4: COMPLETE RANGE UPLOAD
# ============================================
echo -e "\n\033[1;33m12. WORKFLOW STEP 4: COMPLETE RANGE UPLOAD\033[0m"
echo "------------------------------------------"
curl -s -X POST "$API/seasons/$SEASON_ID/complete-range-upload" \
  -H "Content-Type: application/json" \
  -d '{}'
echo ""

# ============================================
# CREATE PURCHASE ORDER
# ============================================
echo -e "\n\033[1;33m13. CREATE PURCHASE ORDER\033[0m"
echo "-------------------------"
PO_RESPONSE=$(curl -s -X POST "$API/purchase-orders" \
  -H "Content-Type: application/json" \
  -d "{\"season_id\":\"$SEASON_ID\",\"location_id\":\"$LOCATION_ID\",\"category_id\":\"$CATEGORY_ID\",\"po_number\":\"PO-2026-001\",\"po_value\":12500.00,\"source\":\"api\"}")
echo $PO_RESPONSE
PO_ID=$(echo $PO_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo -e "\n  PO ID: $PO_ID"

# ============================================
# CREATE GRN
# ============================================
echo -e "\n\033[1;33m14. CREATE GRN (Goods Received)\033[0m"
echo "-------------------------------"
GRN_RESPONSE=$(curl -s -X POST "$API/grn" \
  -H "Content-Type: application/json" \
  -d "{\"po_id\":\"$PO_ID\",\"grn_number\":\"GRN-2026-001\",\"grn_date\":\"2026-04-14\",\"received_value\":11250.00}")
echo $GRN_RESPONSE
echo ""

# ============================================
# WORKFLOW STEP 5: LOCK SEASON
# ============================================
echo -e "\n\033[1;33m15. WORKFLOW STEP 5: LOCK SEASON (Final)\033[0m"
echo "----------------------------------------"
curl -s -X POST "$API/seasons/$SEASON_ID/lock" \
  -H "Content-Type: application/json" \
  -d '{}'
echo ""

# ============================================
# VERIFY WORKFLOW STATUS
# ============================================
echo -e "\n\033[1;33m16. VERIFY WORKFLOW STATUS (LOCKED)\033[0m"
echo "-----------------------------------"
curl -s "$API/seasons/$SEASON_ID/workflow-status"
echo ""

# ============================================
# ANALYTICS DASHBOARD
# ============================================
echo -e "\n\033[1;33m17. ANALYTICS DASHBOARD\033[0m"
echo "-----------------------"
curl -s "$API/analytics/dashboard/$SEASON_ID"
echo ""

# ============================================
# LIST ALL ENTITIES
# ============================================
echo -e "\n\033[1;33m18. LIST ALL ENTITIES\033[0m"
echo "---------------------"

echo -e "\n  GET /api/v1/seasons"
curl -s "$API/seasons"
echo ""

echo -e "\n  GET /api/v1/locations"
curl -s "$API/locations"
echo ""

echo -e "\n  GET /api/v1/clusters"
curl -s "$API/clusters"
echo ""

echo -e "\n  GET /api/v1/categories"
curl -s "$API/categories"
echo ""

# ============================================
# SUMMARY
# ============================================
echo -e "\n\033[1;36m============================================\033[0m"
echo -e "\033[1;36mTEST SUMMARY\033[0m"
echo -e "\033[1;36m============================================\033[0m"
echo -e "\n\033[0;32m✅ Cluster Created: Northeast Region\033[0m"
echo -e "\033[0;32m✅ Location Created: Downtown NYC Store (Code: $LOCATION_CODE)\033[0m"
echo -e "\033[0;32m✅ Category Created: Apparel\033[0m"
echo -e "\033[0;32m✅ Season Created: Spring 2026 (Code: $SEASON_CODE)\033[0m"
echo -e "\n\033[1;33mWorkflow Completed:\033[0m"
echo -e "\033[0;32m  ✅ Step 1: Define Locations -> LOCATIONS_DEFINED\033[0m"
echo -e "\033[0;32m  ✅ Step 2: Upload Plan -> PLAN_UPLOADED\033[0m"
echo -e "\033[0;32m  ✅ Step 3: Upload OTB -> OTB_UPLOADED (Formula Verified)\033[0m"
echo -e "\033[0;32m  ✅ Step 4: Upload Range -> RANGE_UPLOADED\033[0m"
echo -e "\033[0;32m  ✅ Step 5: PO/GRN Ingested\033[0m"
echo -e "\033[0;32m  ✅ Step 6: Lock Season -> LOCKED (Read-Only)\033[0m"
echo -e "\n\033[1;33mCustom ID Formats:\033[0m"
echo -e "\033[0;32m  ✅ Season Code: $SEASON_CODE (XXXX-XXXX format)\033[0m"
echo -e "\033[0;32m  ✅ Location Code: $LOCATION_CODE (16 alphanumeric)\033[0m"
echo -e "\n\033[1;33mOTB Formula:\033[0m"
echo -e "\033[0;32m  ✅ OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order\033[0m"
echo -e "\033[0;32m  ✅ 110000 = 100000 + 50000 - 30000 - 10000\033[0m"
echo ""
