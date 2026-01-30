#!/usr/bin/env pwsh
# Kyros Backend - CURL Test Script
# Run: ./curl_tests.ps1

$BASE_URL = "http://localhost:8000"
$API = "$BASE_URL/api/v1"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "KYROS BACKEND - CURL API TESTS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Base URL: $BASE_URL" -ForegroundColor Gray
Write-Host ""

# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================
Write-Host "1. HEALTH CHECK ENDPOINTS" -ForegroundColor Yellow
Write-Host "-------------------------"

Write-Host "`n  GET /" -ForegroundColor Green
curl.exe -s $BASE_URL/

Write-Host "`n`n  GET /health" -ForegroundColor Green
curl.exe -s $BASE_URL/health

Write-Host "`n`n  GET /ready" -ForegroundColor Green
curl.exe -s $BASE_URL/ready

# ============================================
# SEASON ENDPOINTS
# ============================================
Write-Host "`n`n2. SEASON ENDPOINTS" -ForegroundColor Yellow
Write-Host "-------------------"

Write-Host "`n  GET /api/v1/seasons - List all seasons" -ForegroundColor Green
curl.exe -s "$API/seasons"

Write-Host "`n`n  POST /api/v1/seasons - Create a season" -ForegroundColor Green
Write-Host "  Body: {name, start_date, end_date}" -ForegroundColor Gray
@'
{
  "name": "Spring 2026",
  "start_date": "2026-03-01",
  "end_date": "2026-05-31"
}
'@ | Out-File -Encoding ascii -NoNewline temp_season.json
curl.exe -s -X POST "$API/seasons" -H "Content-Type: application/json" -d "@temp_season.json"

Write-Host "`n`n  GET /api/v1/seasons/{id} - Get season by ID" -ForegroundColor Green
Write-Host "  (Replace {id} with actual UUID)" -ForegroundColor Gray
# curl.exe -s "$API/seasons/YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/seasons/{id}/workflow-status - Get workflow status" -ForegroundColor Green
# curl.exe -s "$API/seasons/YOUR-SEASON-UUID/workflow-status"

Write-Host "`n`n  POST /api/v1/seasons/{id}/define-locations - Start location definition" -ForegroundColor Green
# curl.exe -s -X POST "$API/seasons/YOUR-SEASON-UUID/define-locations"

Write-Host "`n`n  POST /api/v1/seasons/{id}/complete-plan-upload - Complete plan upload" -ForegroundColor Green
# curl.exe -s -X POST "$API/seasons/YOUR-SEASON-UUID/complete-plan-upload"

Write-Host "`n`n  POST /api/v1/seasons/{id}/complete-otb-upload - Complete OTB upload" -ForegroundColor Green
# curl.exe -s -X POST "$API/seasons/YOUR-SEASON-UUID/complete-otb-upload"

Write-Host "`n`n  POST /api/v1/seasons/{id}/complete-range-upload - Complete range intent upload" -ForegroundColor Green
# curl.exe -s -X POST "$API/seasons/YOUR-SEASON-UUID/complete-range-upload"

Write-Host "`n`n  POST /api/v1/seasons/{id}/lock - Lock season (final step)" -ForegroundColor Green
# curl.exe -s -X POST "$API/seasons/YOUR-SEASON-UUID/lock"

# ============================================
# LOCATION ENDPOINTS
# ============================================
Write-Host "`n`n3. LOCATION ENDPOINTS" -ForegroundColor Yellow
Write-Host "---------------------"

Write-Host "`n  GET /api/v1/locations - List all locations" -ForegroundColor Green
curl.exe -s "$API/locations"

Write-Host "`n`n  GET /api/v1/locations/stores - List stores only" -ForegroundColor Green
curl.exe -s "$API/locations/stores"

Write-Host "`n`n  GET /api/v1/locations/warehouses - List warehouses only" -ForegroundColor Green
curl.exe -s "$API/locations/warehouses"

Write-Host "`n`n  POST /api/v1/locations - Create a location" -ForegroundColor Green
Write-Host "  Body: {name, type, cluster_id}" -ForegroundColor Gray
@'
{
  "name": "Downtown Store",
  "type": "store",
  "cluster_id": "YOUR-CLUSTER-UUID",
  "address": "123 Main St",
  "city": "New York",
  "country": "USA"
}
'@ | Out-File -Encoding ascii -NoNewline temp_location.json
# curl.exe -s -X POST "$API/locations" -H "Content-Type: application/json" -d "@temp_location.json"

Write-Host "`n`n  POST /api/v1/locations/bulk - Bulk create locations" -ForegroundColor Green
# curl.exe -s -X POST "$API/locations/bulk" -H "Content-Type: application/json" -d "@locations_bulk.json"

# ============================================
# CLUSTER ENDPOINTS
# ============================================
Write-Host "`n`n4. CLUSTER ENDPOINTS" -ForegroundColor Yellow
Write-Host "--------------------"

Write-Host "`n  GET /api/v1/clusters - List all clusters" -ForegroundColor Green
curl.exe -s "$API/clusters"

Write-Host "`n`n  POST /api/v1/clusters - Create a cluster" -ForegroundColor Green
@'
{
  "name": "Northeast Region",
  "description": "Stores in the northeastern United States"
}
'@ | Out-File -Encoding ascii -NoNewline temp_cluster.json
curl.exe -s -X POST "$API/clusters" -H "Content-Type: application/json" -d "@temp_cluster.json"

# ============================================
# CATEGORY ENDPOINTS
# ============================================
Write-Host "`n`n5. CATEGORY ENDPOINTS" -ForegroundColor Yellow
Write-Host "---------------------"

Write-Host "`n  GET /api/v1/categories - List all categories" -ForegroundColor Green
curl.exe -s "$API/categories"

Write-Host "`n`n  GET /api/v1/categories/tree - Get category tree" -ForegroundColor Green
curl.exe -s "$API/categories/tree"

Write-Host "`n`n  POST /api/v1/categories - Create a category" -ForegroundColor Green
@'
{
  "name": "Apparel",
  "code": "APP",
  "description": "Clothing and accessories"
}
'@ | Out-File -Encoding ascii -NoNewline temp_category.json
curl.exe -s -X POST "$API/categories" -H "Content-Type: application/json" -d "@temp_category.json"

# ============================================
# SEASON PLAN ENDPOINTS
# ============================================
Write-Host "`n`n6. SEASON PLAN ENDPOINTS" -ForegroundColor Yellow
Write-Host "------------------------"

Write-Host "`n  GET /api/v1/plans?season_id={id} - List plans for a season" -ForegroundColor Green
# curl.exe -s "$API/plans?season_id=YOUR-SEASON-UUID"

Write-Host "`n`n  POST /api/v1/plans - Create a plan" -ForegroundColor Green
@'
{
  "season_id": "YOUR-SEASON-UUID",
  "location_id": "YOUR-LOCATION-UUID",
  "category_id": "YOUR-CATEGORY-UUID",
  "planned_quantity": 1000,
  "planned_amount": 50000.00
}
'@ | Out-File -Encoding ascii -NoNewline temp_plan.json
# curl.exe -s -X POST "$API/plans" -H "Content-Type: application/json" -d "@temp_plan.json"

Write-Host "`n`n  POST /api/v1/plans/bulk - Bulk create plans" -ForegroundColor Green
# curl.exe -s -X POST "$API/plans/bulk" -H "Content-Type: application/json" -d "@plans_bulk.json"

Write-Host "`n`n  POST /api/v1/plans/approve - Approve plans (makes immutable)" -ForegroundColor Green
# curl.exe -s -X POST "$API/plans/approve" -H "Content-Type: application/json" -d '{"plan_ids": ["uuid1", "uuid2"]}'

# ============================================
# OTB PLAN ENDPOINTS
# ============================================
Write-Host "`n`n7. OTB PLAN ENDPOINTS" -ForegroundColor Yellow
Write-Host "---------------------"
Write-Host "  Formula: OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order" -ForegroundColor Gray

Write-Host "`n  GET /api/v1/otb?season_id={id} - List OTB plans for a season" -ForegroundColor Green
# curl.exe -s "$API/otb?season_id=YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/otb/summary - Get OTB summary" -ForegroundColor Green
curl.exe -s "$API/otb/summary"

Write-Host "`n`n  POST /api/v1/otb - Create an OTB plan (auto-calculates OTB)" -ForegroundColor Green
@'
{
  "season_id": "YOUR-SEASON-UUID",
  "category_id": "YOUR-CATEGORY-UUID",
  "location_id": "YOUR-LOCATION-UUID",
  "planned_sales": 100000.00,
  "planned_closing_stock": 50000.00,
  "opening_stock": 30000.00,
  "on_order": 10000.00
}
'@ | Out-File -Encoding ascii -NoNewline temp_otb.json
# curl.exe -s -X POST "$API/otb" -H "Content-Type: application/json" -d "@temp_otb.json"

# ============================================
# RANGE INTENT ENDPOINTS
# ============================================
Write-Host "`n`n8. RANGE INTENT ENDPOINTS" -ForegroundColor Yellow
Write-Host "-------------------------"

Write-Host "`n  GET /api/v1/range-intent?season_id={id} - List range intents" -ForegroundColor Green
# curl.exe -s "$API/range-intent?season_id=YOUR-SEASON-UUID"

Write-Host "`n`n  POST /api/v1/range-intent - Create a range intent" -ForegroundColor Green
@'
{
  "season_id": "YOUR-SEASON-UUID",
  "category_id": "YOUR-CATEGORY-UUID",
  "target_option_count": 50,
  "target_sku_count": 200,
  "price_band_low": 29.99,
  "price_band_high": 99.99
}
'@ | Out-File -Encoding ascii -NoNewline temp_range.json
# curl.exe -s -X POST "$API/range-intent" -H "Content-Type: application/json" -d "@temp_range.json"

# ============================================
# PURCHASE ORDER ENDPOINTS
# ============================================
Write-Host "`n`n9. PURCHASE ORDER ENDPOINTS" -ForegroundColor Yellow
Write-Host "---------------------------"

Write-Host "`n  GET /api/v1/purchase-orders - List all purchase orders" -ForegroundColor Green
curl.exe -s "$API/purchase-orders"

Write-Host "`n`n  GET /api/v1/purchase-orders/summary - Get PO summary" -ForegroundColor Green
curl.exe -s "$API/purchase-orders/summary"

Write-Host "`n`n  GET /api/v1/purchase-orders/by-number/{po_number} - Get PO by number" -ForegroundColor Green
# curl.exe -s "$API/purchase-orders/by-number/PO-20260130-XXXXXX"

Write-Host "`n`n  POST /api/v1/purchase-orders - Create a purchase order" -ForegroundColor Green
@'
{
  "season_id": "YOUR-SEASON-UUID",
  "supplier_id": "YOUR-SUPPLIER-UUID",
  "category_id": "YOUR-CATEGORY-UUID",
  "location_id": "YOUR-LOCATION-UUID",
  "quantity": 500,
  "unit_cost": 25.00,
  "expected_delivery_date": "2026-04-15"
}
'@ | Out-File -Encoding ascii -NoNewline temp_po.json
# curl.exe -s -X POST "$API/purchase-orders" -H "Content-Type: application/json" -d "@temp_po.json"

# ============================================
# GRN ENDPOINTS
# ============================================
Write-Host "`n`n10. GRN (GOODS RECEIVED NOTE) ENDPOINTS" -ForegroundColor Yellow
Write-Host "---------------------------------------"

Write-Host "`n  GET /api/v1/grn?po_id={id} - List GRN records for a PO" -ForegroundColor Green
# curl.exe -s "$API/grn?po_id=YOUR-PO-UUID"

Write-Host "`n`n  GET /api/v1/grn?start_date=2026-01-01&end_date=2026-12-31 - List by date range" -ForegroundColor Green
# curl.exe -s "$API/grn?start_date=2026-01-01&end_date=2026-12-31"

Write-Host "`n`n  GET /api/v1/grn/summary - Get GRN summary" -ForegroundColor Green
curl.exe -s "$API/grn/summary"

Write-Host "`n`n  GET /api/v1/grn/fulfillment/{po_id} - Get PO fulfillment status" -ForegroundColor Green
# curl.exe -s "$API/grn/fulfillment/YOUR-PO-UUID"

Write-Host "`n`n  POST /api/v1/grn - Create a GRN record" -ForegroundColor Green
@'
{
  "po_id": "YOUR-PO-UUID",
  "received_quantity": 450,
  "received_date": "2026-04-14",
  "quality_status": "accepted",
  "notes": "Shipment received in good condition"
}
'@ | Out-File -Encoding ascii -NoNewline temp_grn.json
# curl.exe -s -X POST "$API/grn" -H "Content-Type: application/json" -d "@temp_grn.json"

# ============================================
# ANALYTICS ENDPOINTS
# ============================================
Write-Host "`n`n11. ANALYTICS ENDPOINTS" -ForegroundColor Yellow
Write-Host "-----------------------"

Write-Host "`n  GET /api/v1/analytics/read-only-view/{season_id} - READ-ONLY ANALYTICS VIEW" -ForegroundColor Green
Write-Host "  (Final workflow step - available after season is LOCKED)" -ForegroundColor Gray
# curl.exe -s "$API/analytics/read-only-view/YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/analytics/dashboard/{season_id} - Dashboard summary" -ForegroundColor Green
# curl.exe -s "$API/analytics/dashboard/YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/analytics/budget-vs-actual/{season_id} - Budget vs Actual" -ForegroundColor Green
# curl.exe -s "$API/analytics/budget-vs-actual/YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/analytics/category-breakdown/{season_id} - Category breakdown" -ForegroundColor Green
# curl.exe -s "$API/analytics/category-breakdown/YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/analytics/cluster-summary/{season_id} - Cluster summary" -ForegroundColor Green
# curl.exe -s "$API/analytics/cluster-summary/YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/analytics/location-performance/{season_id} - Location performance" -ForegroundColor Green
# curl.exe -s "$API/analytics/location-performance/YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/analytics/po-status/{season_id} - PO status" -ForegroundColor Green
# curl.exe -s "$API/analytics/po-status/YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/analytics/price-band-analysis/{season_id} - Price band analysis" -ForegroundColor Green
# curl.exe -s "$API/analytics/price-band-analysis/YOUR-SEASON-UUID"

Write-Host "`n`n  GET /api/v1/analytics/workflow-status - All workflows status" -ForegroundColor Green
curl.exe -s "$API/analytics/workflow-status"

Write-Host "`n`n  GET /api/v1/analytics/export/{season_id}?format=json - Export analytics" -ForegroundColor Green
# curl.exe -s "$API/analytics/export/YOUR-SEASON-UUID?format=json"

# ============================================
# USER ENDPOINTS
# ============================================
Write-Host "`n`n12. USER ENDPOINTS" -ForegroundColor Yellow
Write-Host "------------------"

Write-Host "`n  GET /api/v1/users - List all users" -ForegroundColor Green
curl.exe -s "$API/users"

Write-Host "`n`n  GET /api/v1/users/{id} - Get user by ID" -ForegroundColor Green
# curl.exe -s "$API/users/YOUR-USER-UUID"

# ============================================
# CLEANUP
# ============================================
Remove-Item -Force temp_*.json -ErrorAction SilentlyContinue

Write-Host "`n`n============================================" -ForegroundColor Cyan
Write-Host "CURL TESTING COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "`nNote: DB-dependent endpoints will fail if PostgreSQL is not running." -ForegroundColor Gray
Write-Host "Start PostgreSQL and run migrations for full functionality." -ForegroundColor Gray
Write-Host "`nAPI Docs: $BASE_URL/docs" -ForegroundColor Cyan
Write-Host "ReDoc: $BASE_URL/redoc" -ForegroundColor Cyan
