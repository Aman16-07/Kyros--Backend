"""Pydantic schemas package."""

from app.schemas.base import (
    BaseSchema,
    MessageResponse,
    PaginatedResponse,
    TimestampSchema,
    UUIDSchema,
)
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.schemas.season import (
    SeasonCreate,
    SeasonListResponse,
    SeasonResponse,
    SeasonUpdate,
    SeasonWithWorkflow,
    WorkflowResponse,
)
from app.schemas.cluster import (
    ClusterCreate,
    ClusterListResponse,
    ClusterResponse,
    ClusterUpdate,
    ClusterWithLocations,
)
from app.schemas.location import (
    LocationBulkCreate,
    LocationCreate,
    LocationListResponse,
    LocationResponse,
    LocationUpdate,
    LocationWithCluster,
)
from app.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryTree,
    CategoryUpdate,
)
from app.schemas.plan import (
    SeasonPlanApproveRequest,
    SeasonPlanBulkCreate,
    SeasonPlanCreate,
    SeasonPlanListResponse,
    SeasonPlanResponse,
    SeasonPlanUpdate,
    SeasonPlanWithDetails,
)
from app.schemas.otb import (
    OTBPlanBulkCreate,
    OTBPlanCreate,
    OTBPlanListResponse,
    OTBPlanResponse,
    OTBPlanUpdate,
    OTBPlanWithDetails,
    OTBSummary,
)
from app.schemas.range_intent import (
    RangeIntentBulkCreate,
    RangeIntentCreate,
    RangeIntentListResponse,
    RangeIntentResponse,
    RangeIntentUpdate,
    RangeIntentWithDetails,
)
from app.schemas.po import (
    POSummary,
    PurchaseOrderBulkCreate,
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    PurchaseOrderWithDetails,
)
from app.schemas.grn import (
    GRNRecordBulkCreate,
    GRNRecordCreate,
    GRNRecordListResponse,
    GRNRecordResponse,
    GRNRecordUpdate,
    GRNRecordWithPO,
    GRNSummary,
)
# Phase 2
from app.schemas.otb_position import (
    OTBAdjustmentCreate,
    OTBAdjustmentListResponse,
    OTBAdjustmentResponse,
    OTBAlertListResponse,
    OTBConsumptionListResponse,
    OTBDashboardResponse,
    OTBForecastListResponse,
    OTBPositionListResponse,
    OTBPositionResponse,
)
from app.schemas.range_architecture import (
    RangeApproveRequest,
    RangeArchitectureBulkCreate,
    RangeArchitectureCreate,
    RangeArchitectureListResponse,
    RangeArchitectureResponse,
    RangeArchitectureUpdate,
    RangeComparisonResponse,
    RangeRejectRequest,
    RangeSubmitRequest,
)

__all__ = [
    # Base
    "BaseSchema",
    "MessageResponse",
    "PaginatedResponse",
    "TimestampSchema",
    "UUIDSchema",
    # User
    "UserCreate",
    "UserListResponse",
    "UserResponse",
    "UserUpdate",
    # Season
    "SeasonCreate",
    "SeasonListResponse",
    "SeasonResponse",
    "SeasonUpdate",
    "SeasonWithWorkflow",
    "WorkflowResponse",
    # Cluster
    "ClusterCreate",
    "ClusterListResponse",
    "ClusterResponse",
    "ClusterUpdate",
    "ClusterWithLocations",
    # Location
    "LocationBulkCreate",
    "LocationCreate",
    "LocationListResponse",
    "LocationResponse",
    "LocationUpdate",
    "LocationWithCluster",
    # Category
    "CategoryCreate",
    "CategoryListResponse",
    "CategoryResponse",
    "CategoryTree",
    "CategoryUpdate",
    # Season Plan
    "SeasonPlanApproveRequest",
    "SeasonPlanBulkCreate",
    "SeasonPlanCreate",
    "SeasonPlanListResponse",
    "SeasonPlanResponse",
    "SeasonPlanUpdate",
    "SeasonPlanWithDetails",
    # OTB Plan
    "OTBPlanBulkCreate",
    "OTBPlanCreate",
    "OTBPlanListResponse",
    "OTBPlanResponse",
    "OTBPlanUpdate",
    "OTBPlanWithDetails",
    "OTBSummary",
    # Range Intent
    "RangeIntentBulkCreate",
    "RangeIntentCreate",
    "RangeIntentListResponse",
    "RangeIntentResponse",
    "RangeIntentUpdate",
    "RangeIntentWithDetails",
    # Purchase Order
    "POSummary",
    "PurchaseOrderBulkCreate",
    "PurchaseOrderCreate",
    "PurchaseOrderListResponse",
    "PurchaseOrderResponse",
    "PurchaseOrderUpdate",
    "PurchaseOrderWithDetails",
    # GRN
    "GRNRecordBulkCreate",
    "GRNRecordCreate",
    "GRNRecordListResponse",
    "GRNRecordResponse",
    "GRNRecordUpdate",
    "GRNRecordWithPO",
    "GRNSummary",
    # Phase 2 - OTB Management
    "OTBAdjustmentCreate",
    "OTBAdjustmentListResponse",
    "OTBAdjustmentResponse",
    "OTBAlertListResponse",
    "OTBConsumptionListResponse",
    "OTBDashboardResponse",
    "OTBForecastListResponse",
    "OTBPositionListResponse",
    "OTBPositionResponse",
    # Phase 2 - Range Architecture
    "RangeApproveRequest",
    "RangeArchitectureBulkCreate",
    "RangeArchitectureCreate",
    "RangeArchitectureListResponse",
    "RangeArchitectureResponse",
    "RangeArchitectureUpdate",
    "RangeComparisonResponse",
    "RangeRejectRequest",
    "RangeSubmitRequest",
]
