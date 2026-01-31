# Frontend Integration Guide

Complete guide for frontend developers integrating with Kyros Backend API.

---

## Quick Start

### Base URL

```
Development:  http://localhost:8000
Production:   https://api.kyros.example.com
```

### API Prefix

All endpoints are prefixed with `/api/v1/`

```
Full URL Pattern: {BASE_URL}/api/v1/{resource}
Example: http://localhost:8000/api/v1/seasons
```

---

## Authentication

### Current State

The API currently operates without authentication for development purposes.

### Future Implementation

When authentication is enabled:

```javascript
// Include token in all requests
const headers = {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
};
```

---

## HTTP Client Setup

### Axios (Recommended)

```javascript
// api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          console.error('Bad Request:', data.detail);
          break;
        case 404:
          console.error('Not Found:', data.detail);
          break;
        case 422:
          console.error('Validation Error:', data.errors);
          break;
        case 500:
          console.error('Server Error');
          break;
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Fetch API

```javascript
// api/fetch-client.js
const BASE_URL = 'http://localhost:8000/api/v1';

async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };
  
  if (options.body && typeof options.body === 'object') {
    config.body = JSON.stringify(options.body);
  }
  
  const response = await fetch(url, config);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API Error');
  }
  
  return response.json();
}

export const api = {
  get: (endpoint) => apiRequest(endpoint, { method: 'GET' }),
  post: (endpoint, data) => apiRequest(endpoint, { method: 'POST', body: data }),
  put: (endpoint, data) => apiRequest(endpoint, { method: 'PUT', body: data }),
  delete: (endpoint) => apiRequest(endpoint, { method: 'DELETE' }),
};
```

---

## API Services

### Season Service

```javascript
// services/seasonService.js
import apiClient from '../api/client';

export const seasonService = {
  // Get all seasons
  getAll: async (skip = 0, limit = 100) => {
    return apiClient.get(`/seasons?skip=${skip}&limit=${limit}`);
  },
  
  // Get season by ID
  getById: async (id) => {
    return apiClient.get(`/seasons/${id}`);
  },
  
  // Get season by code (e.g., "P5RF-W7OV")
  getByCode: async (code) => {
    return apiClient.get(`/seasons/code/${code}`);
  },
  
  // Create new season
  create: async (seasonData) => {
    // seasonData: { name, year, channel, start_date?, end_date?, notes? }
    return apiClient.post('/seasons', seasonData);
  },
  
  // Update season
  update: async (id, seasonData) => {
    return apiClient.put(`/seasons/${id}`, seasonData);
  },
  
  // Delete season
  delete: async (id) => {
    return apiClient.delete(`/seasons/${id}`);
  },
  
  // Get workflow status
  getWorkflow: async (seasonId) => {
    return apiClient.get(`/seasons/${seasonId}/workflow`);
  },
  
  // Transition workflow
  transition: async (seasonId, targetStatus) => {
    return apiClient.post(`/seasons/${seasonId}/workflow/transition`, {
      target_status: targetStatus
    });
  },
  
  // Lock season
  lock: async (seasonId) => {
    return apiClient.post(`/seasons/${seasonId}/lock`);
  }
};
```

### Location Service

```javascript
// services/locationService.js
import apiClient from '../api/client';

export const locationService = {
  // Get all locations for a season
  getBySeasonId: async (seasonId) => {
    return apiClient.get(`/locations/season/${seasonId}`);
  },
  
  // Create location
  create: async (locationData) => {
    // locationData: { season_id, name, location_type, cluster_id?, address?, notes? }
    return apiClient.post('/locations', locationData);
  },
  
  // Update location
  update: async (id, locationData) => {
    return apiClient.put(`/locations/${id}`, locationData);
  },
  
  // Delete location
  delete: async (id) => {
    return apiClient.delete(`/locations/${id}`);
  },
  
  // Bulk create locations
  bulkCreate: async (locationsArray) => {
    return apiClient.post('/locations/bulk', locationsArray);
  }
};
```

### Plan Service

```javascript
// services/planService.js
import apiClient from '../api/client';

export const planService = {
  // Get plans for a season
  getBySeasonId: async (seasonId) => {
    return apiClient.get(`/plans/season/${seasonId}`);
  },
  
  // Get single plan
  getById: async (id) => {
    return apiClient.get(`/plans/${id}`);
  },
  
  // Create plan
  create: async (planData) => {
    return apiClient.post('/plans', planData);
  },
  
  // Update plan
  update: async (id, planData) => {
    return apiClient.put(`/plans/${id}`, planData);
  },
  
  // Delete plan
  delete: async (id) => {
    return apiClient.delete(`/plans/${id}`);
  },
  
  // Upload plans (bulk)
  bulkUpload: async (seasonId, plansArray) => {
    return apiClient.post(`/plans/season/${seasonId}/upload`, plansArray);
  }
};
```

### OTB Service

```javascript
// services/otbService.js
import apiClient from '../api/client';

export const otbService = {
  // Get OTB for a season
  getBySeasonId: async (seasonId) => {
    return apiClient.get(`/otb/season/${seasonId}`);
  },
  
  // Create OTB record
  create: async (otbData) => {
    // otbData: { season_id, location_id, category_id, 
    //            planned_sales, planned_closing_stock, opening_stock, on_order }
    return apiClient.post('/otb', otbData);
  },
  
  // Calculate OTB (preview without saving)
  calculate: async (otbData) => {
    return apiClient.post('/otb/calculate', otbData);
  },
  
  // Get OTB summary for season
  getSummary: async (seasonId) => {
    return apiClient.get(`/otb/season/${seasonId}/summary`);
  }
};
```

### Analytics Service

```javascript
// services/analyticsService.js
import apiClient from '../api/client';

export const analyticsService = {
  // Season overview
  getSeasonOverview: async (seasonId) => {
    return apiClient.get(`/analytics/seasons/${seasonId}/overview`);
  },
  
  // Budget analysis
  getBudgetAnalysis: async (seasonId) => {
    return apiClient.get(`/analytics/seasons/${seasonId}/budget`);
  },
  
  // Category breakdown
  getCategoryBreakdown: async (seasonId) => {
    return apiClient.get(`/analytics/seasons/${seasonId}/categories`);
  },
  
  // Location performance
  getLocationPerformance: async (seasonId) => {
    return apiClient.get(`/analytics/seasons/${seasonId}/locations`);
  },
  
  // PO vs GRN analysis
  getPoGrnAnalysis: async (seasonId) => {
    return apiClient.get(`/analytics/seasons/${seasonId}/po-grn`);
  }
};
```

---

## React Integration

### React Query (TanStack Query)

```javascript
// hooks/useSeasons.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { seasonService } from '../services/seasonService';

// Get all seasons
export const useSeasons = (skip = 0, limit = 100) => {
  return useQuery({
    queryKey: ['seasons', skip, limit],
    queryFn: () => seasonService.getAll(skip, limit),
  });
};

// Get single season
export const useSeason = (id) => {
  return useQuery({
    queryKey: ['season', id],
    queryFn: () => seasonService.getById(id),
    enabled: !!id,
  });
};

// Create season
export const useCreateSeason = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => seasonService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seasons'] });
    },
  });
};

// Transition workflow
export const useTransitionWorkflow = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ seasonId, targetStatus }) => 
      seasonService.transition(seasonId, targetStatus),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['season', variables.seasonId] });
    },
  });
};
```

### Usage in Component

```jsx
// components/SeasonList.jsx
import { useSeasons, useCreateSeason } from '../hooks/useSeasons';

function SeasonList() {
  const { data: seasons, isLoading, error } = useSeasons();
  const createMutation = useCreateSeason();
  
  const handleCreate = () => {
    createMutation.mutate({
      name: 'Spring 2025',
      year: 2025,
      channel: 'retail'
    });
  };
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      <button onClick={handleCreate} disabled={createMutation.isPending}>
        {createMutation.isPending ? 'Creating...' : 'Create Season'}
      </button>
      
      <ul>
        {seasons.map((season) => (
          <li key={season.id}>
            {season.season_code} - {season.name} ({season.status})
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## TypeScript Interfaces

```typescript
// types/api.ts

// Enums
export enum SeasonStatus {
  CREATED = 'CREATED',
  LOCATIONS_DEFINED = 'LOCATIONS_DEFINED',
  PLAN_UPLOADED = 'PLAN_UPLOADED',
  OTB_UPLOADED = 'OTB_UPLOADED',
  RANGE_UPLOADED = 'RANGE_UPLOADED',
  LOCKED = 'LOCKED'
}

export enum LocationType {
  WAREHOUSE = 'WAREHOUSE',
  STORE = 'STORE',
  DISTRIBUTION_CENTER = 'DISTRIBUTION_CENTER',
  FRANCHISE = 'FRANCHISE',
  ONLINE = 'ONLINE'
}

export enum POSource {
  MANUAL = 'MANUAL',
  SYSTEM = 'SYSTEM',
  IMPORT = 'IMPORT'
}

// Interfaces
export interface Season {
  id: string;
  season_code: string;
  name: string;
  year: number;
  channel: string;
  status: SeasonStatus;
  start_date?: string;
  end_date?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateSeasonRequest {
  name: string;
  year: number;
  channel: string;
  start_date?: string;
  end_date?: string;
  notes?: string;
}

export interface Location {
  id: string;
  location_code: string;
  season_id: string;
  cluster_id?: string;
  name: string;
  location_type: LocationType;
  address?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface Cluster {
  id: string;
  season_id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface Category {
  id: string;
  season_id: string;
  name: string;
  parent_id?: string;
  budget_allocation?: number;
  description?: string;
  created_at: string;
}

export interface SeasonPlan {
  id: string;
  season_id: string;
  location_id: string;
  category_id: string;
  planned_quantity: number;
  planned_value: number;
  notes?: string;
  created_at: string;
}

export interface OTBPlan {
  id: string;
  season_id: string;
  location_id: string;
  category_id: string;
  planned_sales: number;
  planned_closing_stock: number;
  opening_stock: number;
  on_order: number;
  approved_spend_limit: number;  // Calculated OTB
  notes?: string;
  created_at: string;
}

export interface RangeIntent {
  id: string;
  season_id: string;
  location_id: string;
  category_id: string;
  sku_count: number;
  min_price: number;
  max_price: number;
  avg_price: number;
  total_value: number;
  notes?: string;
  created_at: string;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  season_id: string;
  location_id: string;
  category_id: string;
  supplier: string;
  order_date: string;
  expected_delivery_date?: string;
  quantity: number;
  unit_cost: number;
  total_value: number;
  status: string;
  source: POSource;
  notes?: string;
  created_at: string;
}

export interface GRNRecord {
  id: string;
  grn_number: string;
  po_id: string;
  received_date: string;
  received_quantity: number;
  accepted_quantity: number;
  rejected_quantity: number;
  notes?: string;
  created_at: string;
}

export interface SeasonWorkflow {
  id: string;
  season_id: string;
  current_status: SeasonStatus;
  locations_defined_at?: string;
  plan_uploaded_at?: string;
  otb_uploaded_at?: string;
  range_uploaded_at?: string;
  locked_at?: string;
  created_at: string;
  updated_at?: string;
}

// Analytics Types
export interface SeasonOverview {
  season: Season;
  total_locations: number;
  total_clusters: number;
  total_categories: number;
  total_plans: number;
  total_otb_budget: number;
  total_po_value: number;
  total_grn_value: number;
}

export interface BudgetAnalysis {
  total_budget: number;
  total_committed: number;
  total_received: number;
  budget_utilization_pct: number;
  fulfillment_pct: number;
}
```

---

## Workflow Integration

### Workflow States

```javascript
// constants/workflow.js

export const WORKFLOW_STATES = {
  CREATED: 'CREATED',
  LOCATIONS_DEFINED: 'LOCATIONS_DEFINED',
  PLAN_UPLOADED: 'PLAN_UPLOADED',
  OTB_UPLOADED: 'OTB_UPLOADED',
  RANGE_UPLOADED: 'RANGE_UPLOADED',
  LOCKED: 'LOCKED'
};

export const WORKFLOW_TRANSITIONS = {
  [WORKFLOW_STATES.CREATED]: {
    next: WORKFLOW_STATES.LOCATIONS_DEFINED,
    action: 'Define Locations',
    canEdit: ['locations', 'clusters']
  },
  [WORKFLOW_STATES.LOCATIONS_DEFINED]: {
    next: WORKFLOW_STATES.PLAN_UPLOADED,
    action: 'Upload Plans',
    canEdit: ['plans']
  },
  [WORKFLOW_STATES.PLAN_UPLOADED]: {
    next: WORKFLOW_STATES.OTB_UPLOADED,
    action: 'Upload OTB',
    canEdit: ['otb']
  },
  [WORKFLOW_STATES.OTB_UPLOADED]: {
    next: WORKFLOW_STATES.RANGE_UPLOADED,
    action: 'Upload Range Intent',
    canEdit: ['range_intent']
  },
  [WORKFLOW_STATES.RANGE_UPLOADED]: {
    next: WORKFLOW_STATES.LOCKED,
    action: 'Lock Season',
    canEdit: ['purchase_orders']
  },
  [WORKFLOW_STATES.LOCKED]: {
    next: null,
    action: null,
    canEdit: ['grn']
  }
};

// Helper functions
export const canEditEntity = (status, entity) => {
  return WORKFLOW_TRANSITIONS[status]?.canEdit?.includes(entity) ?? false;
};

export const getNextTransition = (status) => {
  return WORKFLOW_TRANSITIONS[status]?.next;
};
```

### Workflow Component

```jsx
// components/WorkflowProgress.jsx
import { WORKFLOW_STATES, WORKFLOW_TRANSITIONS } from '../constants/workflow';

function WorkflowProgress({ currentStatus, onTransition }) {
  const steps = Object.values(WORKFLOW_STATES);
  const currentIndex = steps.indexOf(currentStatus);
  const nextStatus = WORKFLOW_TRANSITIONS[currentStatus]?.next;
  
  return (
    <div className="workflow-progress">
      <div className="steps">
        {steps.map((step, index) => (
          <div 
            key={step}
            className={`step ${index <= currentIndex ? 'completed' : ''} ${index === currentIndex ? 'current' : ''}`}
          >
            <span className="step-indicator">{index + 1}</span>
            <span className="step-label">{step.replace('_', ' ')}</span>
          </div>
        ))}
      </div>
      
      {nextStatus && (
        <button 
          onClick={() => onTransition(nextStatus)}
          className="transition-button"
        >
          {WORKFLOW_TRANSITIONS[currentStatus].action}
        </button>
      )}
    </div>
  );
}
```

---

## OTB Calculator

### OTB Formula

```
OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order
```

### OTB Calculator Component

```jsx
// components/OTBCalculator.jsx
import { useState, useMemo } from 'react';
import { otbService } from '../services/otbService';

function OTBCalculator({ seasonId, locationId, categoryId, onSave }) {
  const [values, setValues] = useState({
    planned_sales: 0,
    planned_closing_stock: 0,
    opening_stock: 0,
    on_order: 0
  });
  
  // Calculate OTB in real-time
  const calculatedOTB = useMemo(() => {
    return (
      values.planned_sales + 
      values.planned_closing_stock - 
      values.opening_stock - 
      values.on_order
    );
  }, [values]);
  
  const handleChange = (field, value) => {
    setValues(prev => ({
      ...prev,
      [field]: parseFloat(value) || 0
    }));
  };
  
  const handleSave = async () => {
    const data = {
      season_id: seasonId,
      location_id: locationId,
      category_id: categoryId,
      ...values
    };
    
    const result = await otbService.create(data);
    onSave(result);
  };
  
  return (
    <div className="otb-calculator">
      <div className="input-group">
        <label>Planned Sales</label>
        <input
          type="number"
          value={values.planned_sales}
          onChange={(e) => handleChange('planned_sales', e.target.value)}
        />
      </div>
      
      <div className="input-group">
        <label>Planned Closing Stock</label>
        <input
          type="number"
          value={values.planned_closing_stock}
          onChange={(e) => handleChange('planned_closing_stock', e.target.value)}
        />
      </div>
      
      <div className="input-group">
        <label>Opening Stock</label>
        <input
          type="number"
          value={values.opening_stock}
          onChange={(e) => handleChange('opening_stock', e.target.value)}
        />
      </div>
      
      <div className="input-group">
        <label>On Order</label>
        <input
          type="number"
          value={values.on_order}
          onChange={(e) => handleChange('on_order', e.target.value)}
        />
      </div>
      
      <div className="calculated-result">
        <strong>OTB (Approved Spend Limit):</strong>
        <span className={calculatedOTB >= 0 ? 'positive' : 'negative'}>
          ${calculatedOTB.toLocaleString()}
        </span>
      </div>
      
      <button onClick={handleSave}>Save OTB</button>
    </div>
  );
}
```

---

## Error Handling

### Error Response Format

```javascript
// 400 Bad Request
{
  "detail": "Season not found"
}

// 422 Validation Error
{
  "detail": "Validation Error",
  "errors": [
    {
      "field": "body.name",
      "message": "Field required",
      "type": "missing"
    }
  ]
}

// 500 Server Error
{
  "detail": "An unexpected error occurred"
}
```

### Error Handler Component

```jsx
// components/ApiErrorBoundary.jsx
import { Component } from 'react';

class ApiErrorBoundary extends Component {
  state = { hasError: false, error: null };
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-container">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false })}>
            Try Again
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

---

## CORS Configuration

The backend allows CORS from all origins in development:

```python
# Backend CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

No special CORS handling needed on frontend for development.

---

## Testing

### Mock API for Development

```javascript
// mocks/handlers.js (MSW)
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/v1/seasons', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: '123e4567-e89b-12d3-a456-426614174000',
          season_code: 'P5RF-W7OV',
          name: 'Spring 2025',
          year: 2025,
          channel: 'retail',
          status: 'CREATED'
        }
      ])
    );
  }),
  
  rest.post('/api/v1/seasons', (req, res, ctx) => {
    return res(
      ctx.json({
        id: '123e4567-e89b-12d3-a456-426614174001',
        season_code: 'XY12-AB34',
        ...req.body,
        status: 'CREATED'
      })
    );
  })
];
```

---

## Recommended Libraries

| Purpose | Library | Version |
|---------|---------|---------|
| HTTP Client | axios | ^1.6+ |
| State Management | @tanstack/react-query | ^5.0+ |
| Forms | react-hook-form | ^7.0+ |
| Validation | zod | ^3.0+ |
| Date Handling | date-fns | ^3.0+ |
| UI Components | shadcn/ui | latest |
| Routing | react-router-dom | ^6.0+ |
| API Mocking | msw | ^2.0+ |
