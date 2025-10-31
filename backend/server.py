from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from elasticsearch import AsyncElasticsearch
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Elasticsearch connection
es_host = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
es_client = AsyncElasticsearch([es_host])

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Elasticsearch Models
class ProductionOrderCreate(BaseModel):
    data: Dict[str, Any]

class TraceabilityCreate(BaseModel):
    data: Dict[str, Any]

class NameplateCreate(BaseModel):
    data: Dict[str, Any]

class SearchQuery(BaseModel):
    query: str
    index: str = "production_orders_v1"
    size: int = 10

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Elasticsearch Routes

# Health Check
@api_router.get("/elasticsearch/health")
async def elasticsearch_health():
    try:
        health = await es_client.cluster.health()
        return {"status": "connected", "cluster_health": health}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch connection failed: {str(e)}")

# Create Indices
@api_router.post("/elasticsearch/indices/create")
async def create_indices():
    try:
        # Production Orders Index
        production_orders_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "identity_number": {"type": "keyword"},
                    "product_code": {"type": "keyword"},
                    "customer_id": {"type": "integer"},
                    "product_work_center_id": {"type": "integer"},
                    "shift_id": {"type": "integer"},
                    "planning_date": {"type": "date"},
                    "qty": {"type": "integer"},
                    "overtime": {"type": "integer"},
                    "plant_id": {"type": "integer"},
                    "standard_packing_qty": {"type": "integer"},
                    "status_id": {"type": "integer"},
                    "created_by": {"type": "integer"},
                    "modified_by": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "actual_qty": {"type": "object", "enabled": True},
                    "traceabilities": {
                        "type": "nested",
                        "properties": {
                            "id": {"type": "integer"},
                            "model_type": {"type": "keyword"},
                            "model_id": {"type": "integer"},
                            "station_id": {"type": "integer"},
                            "user_id": {"type": "integer"},
                            "content": {"type": "object"},
                            "status_id": {"type": "integer"},
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"},
                            "model": {"type": "object", "enabled": True},
                            "station": {"type": "object", "enabled": True},
                            "status": {"type": "object", "enabled": True}
                        }
                    },
                    "customer": {"type": "object", "enabled": True},
                    "plant": {"type": "object", "enabled": True},
                    "shift": {"type": "object", "enabled": True},
                    "product_work_center": {"type": "object", "enabled": True},
                    "status": {"type": "object", "enabled": True},
                    "packing_boxes": {"type": "nested"},
                    "crew": {"type": "object", "enabled": True}
                }
            }
        }
        
        # Traceabilities Index
        traceabilities_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "model_type": {"type": "keyword"},
                    "model_id": {"type": "integer"},
                    "station_id": {"type": "integer"},
                    "user_id": {"type": "integer"},
                    "content": {"type": "object"},
                    "status_id": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "production_order_id": {"type": "integer"},
                    "model": {"type": "object", "enabled": True},
                    "station": {"type": "object", "enabled": True},
                    "status": {"type": "object", "enabled": True}
                }
            }
        }
        
        # Nameplates Index
        nameplates_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "flag": {"type": "keyword"},
                    "production_order_id": {"type": "integer"},
                    "identity_number": {"type": "keyword"},
                    "shift_id": {"type": "integer"},
                    "user_id": {"type": "integer"},
                    "product_work_center_id": {"type": "integer"},
                    "station_id": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "production_order": {"type": "object", "enabled": True},
                    "product_work_center": {"type": "object", "enabled": True}
                }
            }
        }
        
        results = []
        
        # Create indices
        if not await es_client.indices.exists(index="production_orders_v1"):
            await es_client.indices.create(index="production_orders_v1", body=production_orders_mapping)
            results.append("production_orders_v1 created")
        else:
            results.append("production_orders_v1 already exists")
            
        if not await es_client.indices.exists(index="traceabilities_v1"):
            await es_client.indices.create(index="traceabilities_v1", body=traceabilities_mapping)
            results.append("traceabilities_v1 created")
        else:
            results.append("traceabilities_v1 already exists")
            
        if not await es_client.indices.exists(index="nameplates_v1"):
            await es_client.indices.create(index="nameplates_v1", body=nameplates_mapping)
            results.append("nameplates_v1 created")
        else:
            results.append("nameplates_v1 already exists")
        
        return {"message": "Indices created successfully", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create indices: {str(e)}")

# Production Orders CRUD
@api_router.post("/elasticsearch/production-orders")
async def create_production_order(order: ProductionOrderCreate):
    try:
        result = await es_client.index(
            index="production_orders_v1",
            document=order.data,
            id=order.data.get("id")
        )
        return {"message": "Production order created", "id": result["_id"], "result": result["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create production order: {str(e)}")

@api_router.get("/elasticsearch/production-orders/{order_id}")
async def get_production_order(order_id: int):
    try:
        result = await es_client.get(index="production_orders_v1", id=order_id)
        return result["_source"]
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Production order not found: {str(e)}")

@api_router.get("/elasticsearch/production-orders")
async def list_production_orders(size: int = 100):
    try:
        result = await es_client.search(
            index="production_orders_v1",
            body={
                "query": {"match_all": {}},
                "size": size,
                "sort": [{"id": {"order": "desc"}}]
            }
        )
        return {
            "total": result["hits"]["total"]["value"],
            "data": [hit["_source"] for hit in result["hits"]["hits"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list production orders: {str(e)}")

@api_router.put("/elasticsearch/production-orders/{order_id}")
async def update_production_order(order_id: int, order: ProductionOrderCreate):
    try:
        result = await es_client.update(
            index="production_orders_v1",
            id=order_id,
            body={"doc": order.data}
        )
        return {"message": "Production order updated", "result": result["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update production order: {str(e)}")

@api_router.delete("/elasticsearch/production-orders/{order_id}")
async def delete_production_order(order_id: int):
    try:
        result = await es_client.delete(index="production_orders_v1", id=order_id)
        return {"message": "Production order deleted", "result": result["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete production order: {str(e)}")

# Traceabilities CRUD
@api_router.post("/elasticsearch/traceabilities")
async def create_traceability(trace: TraceabilityCreate):
    try:
        result = await es_client.index(
            index="traceabilities_v1",
            document=trace.data,
            id=trace.data.get("id")
        )
        return {"message": "Traceability created", "id": result["_id"], "result": result["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create traceability: {str(e)}")

@api_router.get("/elasticsearch/traceabilities/{trace_id}")
async def get_traceability(trace_id: int):
    try:
        result = await es_client.get(index="traceabilities_v1", id=trace_id)
        return result["_source"]
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Traceability not found: {str(e)}")

@api_router.get("/elasticsearch/traceabilities")
async def list_traceabilities(size: int = 100):
    try:
        result = await es_client.search(
            index="traceabilities_v1",
            body={
                "query": {"match_all": {}},
                "size": size
            }
        )
        return {
            "total": result["hits"]["total"]["value"],
            "data": [hit["_source"] for hit in result["hits"]["hits"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list traceabilities: {str(e)}")

# Nameplates CRUD
@api_router.post("/elasticsearch/nameplates")
async def create_nameplate(nameplate: NameplateCreate):
    try:
        result = await es_client.index(
            index="nameplates_v1",
            document=nameplate.data,
            id=nameplate.data.get("id")
        )
        return {"message": "Nameplate created", "id": result["_id"], "result": result["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create nameplate: {str(e)}")

@api_router.get("/elasticsearch/nameplates/{nameplate_id}")
async def get_nameplate(nameplate_id: int):
    try:
        result = await es_client.get(index="nameplates_v1", id=nameplate_id)
        return result["_source"]
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Nameplate not found: {str(e)}")

@api_router.get("/elasticsearch/nameplates")
async def list_nameplates(size: int = 100):
    try:
        result = await es_client.search(
            index="nameplates_v1",
            body={
                "query": {"match_all": {}},
                "size": size
            }
        )
        return {
            "total": result["hits"]["total"]["value"],
            "data": [hit["_source"] for hit in result["hits"]["hits"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list nameplates: {str(e)}")

# Search Endpoints
@api_router.post("/elasticsearch/search")
async def search(query: SearchQuery):
    try:
        result = await es_client.search(
            index=query.index,
            body={
                "query": {
                    "query_string": {
                        "query": query.query,
                        "default_operator": "AND"
                    }
                },
                "size": query.size
            }
        )
        return {
            "total": result["hits"]["total"]["value"],
            "data": [hit["_source"] for hit in result["hits"]["hits"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Advanced Search - Search by production order identity number
@api_router.get("/elasticsearch/search/production-orders/by-identity/{identity_number}")
async def search_by_identity(identity_number: str):
    try:
        result = await es_client.search(
            index="production_orders_v1",
            body={
                "query": {
                    "term": {
                        "identity_number": identity_number
                    }
                }
            }
        )
        return {
            "total": result["hits"]["total"]["value"],
            "data": [hit["_source"] for hit in result["hits"]["hits"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Search by customer
@api_router.get("/elasticsearch/search/production-orders/by-customer/{customer_id}")
async def search_by_customer(customer_id: int):
    try:
        result = await es_client.search(
            index="production_orders_v1",
            body={
                "query": {
                    "term": {
                        "customer_id": customer_id
                    }
                }
            }
        )
        return {
            "total": result["hits"]["total"]["value"],
            "data": [hit["_source"] for hit in result["hits"]["hits"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Search with nested traceabilities
@api_router.get("/elasticsearch/search/production-orders/by-station/{station_id}")
async def search_by_station(station_id: int):
    try:
        result = await es_client.search(
            index="production_orders_v1",
            body={
                "query": {
                    "nested": {
                        "path": "traceabilities",
                        "query": {
                            "term": {
                                "traceabilities.station_id": station_id
                            }
                        }
                    }
                }
            }
        )
        return {
            "total": result["hits"]["total"]["value"],
            "data": [hit["_source"] for hit in result["hits"]["hits"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    await es_client.close()
