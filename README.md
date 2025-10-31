# Elasticsearch Data Manager

A full-stack application for managing production orders, traceabilities, and nameplates using Elasticsearch with relational indices.

## Features

- **Elasticsearch Integration**: Full CRUD operations with nested document support
- **Relational Indices**: Production Orders, Traceabilities, and Nameplates with relationships
- **Advanced Search**: Query across all indices with nested queries
- **REST API**: FastAPI backend with comprehensive endpoints
- **Modern UI**: React frontend with beautiful interface
- **HTTP Test Files**: Visual Studio Code REST Client compatible

## Tech Stack

- **Backend**: Python FastAPI + Elasticsearch 8.19.2
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Database**: Elasticsearch 8.x
- **Search Engine**: Elasticsearch with nested mappings

## Getting Started

### Prerequisites

- Elasticsearch 8.x running on port 9200
- Python 3.11+
- Node.js 16+

### Installation

1. **Start Elasticsearch**:
```bash
# Elasticsearch is already configured and running
curl http://localhost:9200
```

2. **Backend Setup**:
```bash
cd backend
pip install -r requirements.txt
# Backend runs via supervisor on port 8001
```

3. **Frontend Setup**:
```bash
cd frontend
yarn install
# Frontend runs via supervisor on port 3000
```

### Initialize Indices

Create the Elasticsearch indices:

```bash
curl -X POST http://localhost:8001/api/elasticsearch/indices/create
```

Or use the "Initialize Indices" button in the UI.

## API Endpoints

### Health Check

```bash
# Check Elasticsearch connection
GET http://localhost:8001/api/elasticsearch/health
```

### Production Orders

```bash
# Create
POST http://localhost:8001/api/elasticsearch/production-orders
Content-Type: application/json
{
  "data": {
    "id": 90,
    "identity_number": "2251030001",
    "product_code": "7200-TJ104",
    "customer_id": 65,
    "qty": 100
  }
}

# Get by ID
GET http://localhost:8001/api/elasticsearch/production-orders/90

# List all
GET http://localhost:8001/api/elasticsearch/production-orders?size=100

# Update
PUT http://localhost:8001/api/elasticsearch/production-orders/90
Content-Type: application/json
{
  "data": {
    "qty": 150
  }
}

# Delete
DELETE http://localhost:8001/api/elasticsearch/production-orders/90
```

### Traceabilities

```bash
# Create
POST http://localhost:8001/api/elasticsearch/traceabilities
Content-Type: application/json
{
  "data": {
    "id": 835,
    "model_type": "App\\Models\\Nameplate",
    "station_id": 12,
    "production_order_id": 90
  }
}

# Get by ID
GET http://localhost:8001/api/elasticsearch/traceabilities/835

# List all
GET http://localhost:8001/api/elasticsearch/traceabilities?size=100
```

### Nameplates

```bash
# Create
POST http://localhost:8001/api/elasticsearch/nameplates
Content-Type: application/json
{
  "data": {
    "id": 607,
    "flag": "WH",
    "production_order_id": 91,
    "identity_number": "PR;2251031001-0001"
  }
}

# Get by ID
GET http://localhost:8001/api/elasticsearch/nameplates/607

# List all
GET http://localhost:8001/api/elasticsearch/nameplates?size=100
```

### Advanced Search

```bash
# Generic search
POST http://localhost:8001/api/elasticsearch/search
Content-Type: application/json
{
  "query": "AJI",
  "index": "production_orders_v1",
  "size": 10
}

# Search by identity number
GET http://localhost:8001/api/elasticsearch/search/production-orders/by-identity/2251030001

# Search by customer
GET http://localhost:8001/api/elasticsearch/search/production-orders/by-customer/65

# Search by station (nested query)
GET http://localhost:8001/api/elasticsearch/search/production-orders/by-station/12
```

## Visual Studio HTTP Testing

Use the included `api_tests.http` file with the REST Client extension in Visual Studio Code:

1. Install "REST Client" extension in VS Code
2. Open `/app/api_tests.http`
3. Click "Send Request" above any request

## Index Mappings

### production_orders_v1
- Nested traceabilities array
- Related objects: customer, plant, shift, status
- Supports complex nested queries

### traceabilities_v1
- References production_order_id
- Contains station and status objects
- Supports aggregations

### nameplates_v1
- References production_order_id
- Contains product work center details
- Linked via production_order_id

## UI Features

### Dashboard
- System health monitoring
- Quick access to all sections
- One-click index initialization

### Production Orders
- List and detail views
- Customer information
- Traceability records
- Actual quantity tracking

### Traceabilities
- Station tracking
- Status monitoring
- Model relationships

### Nameplates
- Identity numbers
- Production order linking
- Shift and station data

### Search
- Cross-index search
- Query builder
- Result visualization

## Data Relationships

```
production_orders_v1
├── customer (embedded)
├── plant (embedded)
├── shift (embedded)
├── product_work_center (embedded)
├── status (embedded)
├── crew (embedded)
└── traceabilities (nested array)
    ├── model (embedded)
    ├── station (embedded)
    └── status (embedded)

nameplates_v1
├── production_order_id → production_orders_v1.id
└── product_work_center (embedded)

traceabilities_v1
└── production_order_id → production_orders_v1.id
```

## Example Queries

### Find production orders by customer
```json
{
  "query": {
    "term": {
      "customer_id": 65
    }
  }
}
```

### Find orders with specific traceability station
```json
{
  "query": {
    "nested": {
      "path": "traceabilities",
      "query": {
        "term": {
          "traceabilities.station_id": 12
        }
      }
    }
  }
}
```

### Full-text search across fields
```json
{
  "query": {
    "query_string": {
      "query": "AJI AND K2VM",
      "default_operator": "AND"
    }
  }
}
```

## Architecture

```
Frontend (React)
    ↓
FastAPI Backend
    ↓
Elasticsearch
```

- Frontend makes requests to `/api/elasticsearch/*`
- Backend uses AsyncElasticsearch client
- Data is indexed with nested mappings for relationships
- Queries support nested paths for complex filtering

## Development

### Backend
```bash
# Check backend logs
tail -f /var/log/supervisor/backend.err.log

# Restart backend
sudo supervisorctl restart backend
```

### Frontend
```bash
# Check frontend logs
tail -f /var/log/supervisor/frontend.err.log

# Restart frontend
sudo supervisorctl restart frontend
```

### Elasticsearch
```bash
# Check Elasticsearch status
curl http://localhost:9200/_cluster/health

# List indices
curl http://localhost:9200/_cat/indices

# View index mapping
curl http://localhost:9200/production_orders_v1/_mapping
```

## Troubleshooting

### Elasticsearch not connecting
```bash
# Check if Elasticsearch is running
ps aux | grep elasticsearch

# Restart Elasticsearch
sudo -u elasticsearch ES_JAVA_OPTS="-Xms512m -Xmx512m" /usr/share/elasticsearch/bin/elasticsearch -d
```

### Backend errors
```bash
# View backend logs
tail -100 /var/log/supervisor/backend.err.log

# Test Elasticsearch connection
curl http://localhost:8001/api/elasticsearch/health
```

### Frontend issues
```bash
# Check if frontend is running
sudo supervisorctl status frontend

# View browser console for errors
```

## Sample Data

The application includes sample data structures from production systems:

- **Production Orders**: Manufacturing order tracking
- **Traceabilities**: Quality control checkpoints
- **Nameplates**: Product identification

All indices support the complete data structures provided in the requirements.

## License

MIT

## Support

For issues or questions, check the logs or contact support.
