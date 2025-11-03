from contextlib import asynccontextmanager
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

class ProductionOrderActive(BaseModel):
    shift_id: int
    station_flag: Optional[str] = None
    user_id: Optional[int] = None
    planning_dates: Any
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
                    # "product_work_center": {"type": "object", "enabled": True},
                    "product_work_center": {
                        # "type": "nested",
                        "properties": {
                            "id": {"type": "integer"},
                            "work_center_id": {"type": "integer"},
                            "product_id": {"type": "integer"},
                            "status": {"type": "integer"},
                            "created_by": {"type": "integer"},
                            "modified_by": {"type": "integer"},
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"},
                            "deleted_at": {"type": "date"},
                            "product": {"type": "object", "enabled": True},
                            "work_center": {
                                "type": "nested",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "work_center": {"type": "keyword"},
                                    "description": {"type": "text"},
                                    "created_by": {"type": "integer"},
                                    "modified_by": {"type": "integer"},
                                    "created_at": {"type": "date"},
                                    "updated_at": {"type": "date"},
                                    "deleted_at": {"type": "date"},
                                    "station": {"type": "object", "enabled": True},
                                    "current_station": {
                                        "type": "nested",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "work_center_id": {"type": "integer"},
                                            "flag": {"type": "keyword"},
                                            "station": {"type": "keyword"},
                                            "is_start": {"type": "integer"},
                                            "is_finish": {"type": "integer"},
                                            "ip_address": {"type": "keyword"},
                                            "server_printer": {"type": "keyword"},
                                            "status_printer": {"type": "integer"},
                                            "in_sequence": {"type": "integer"},
                                            "with_integration": {"type": "object", "enabled": True},
                                            "created_by": {"type": "integer"},
                                            "modified_by": {"type": "integer"},
                                            "created_at": {"type": "date"},
                                            "updated_at": {"type": "date"},
                                            "deleted_at": {"type": "date"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "status": {"type": "object", "enabled": True},
                    "packing_boxes": {"type": "nested"},
                    # "crew": {"type": "object", "enabled": True},
                    "crews": {
                        "type": "nested",
                        "properties": {
                            "id": {"type": "integer"},
                            "product_work_center_id": {"type": "integer"},
                            "station_id": {"type": "integer"},
                            "user_id": {"type": "integer"},
                            "plant_id": {"type": "integer"},
                            "type": {"type": "integer"},
                            "created_by": {"type": "integer"},
                            "modified_by": {"type": "integer"},
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"},
                            "station": {"type": "object", "enabled": True},
                            "user": {"type": "object", "enabled": True}
                        }
                    }
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
                    # "production_order_id": {"type": "integer"},
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

@api_router.get("/elasticsearch/production-orders/{id}")
async def get_production_order(id: int):
    try:
        result = await es_client.get(index="production_orders_v1", id=id)
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

@api_router.put("/elasticsearch/production-orders/{id}")
async def update_production_order(id: int, order: ProductionOrderCreate):
    try:
        result = await es_client.update(
            index="production_orders_v1",
            id=id,
            body={"doc": order.data}
        )
        return {"message": "Production order updated", "result": result["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update production order: {str(e)}")

@api_router.delete("/elasticsearch/production-orders/{id}")
async def delete_production_order(id: str):
    try:
        result = await es_client.delete(index="production_orders_v1", id=id)
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
            id=trace.data["model"].get("identity_number")
        )
        return {"message": "Traceability created", "id": result["_id"], "result": result["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create traceability: {str(e)}")

@api_router.get("/elasticsearch/traceabilities/{model_identity_number}")
async def get_traceability(model_identity_number: str):
    try:
        result = await es_client.get(index="traceabilities_v1", id=model_identity_number)
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
            id=nameplate.data.get("identity_number")
        )
        return {"message": "Nameplate created", "id": result["_id"], "result": result["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create nameplate: {str(e)}")

@api_router.get("/elasticsearch/nameplates/{identity_number}")
async def get_nameplate(identity_number: str):
    try:
        result = await es_client.get(index="nameplates_v1", id=identity_number)
        return result["_source"]
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Nameplate not found: {str(e)}")

@api_router.get("/elasticsearch/nameplates")
async def list_nameplates(size: int = 100):
    try:
        # return {"message": "hello world"}
        result = await es_client.search(
            index="nameplates_v1",
            body={
                "query": {"match_all": {}},
                "sort": [
                    {"id": {"order": "desc", "missing": "_last"}}
                ],
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
    # try:
    #     result = await es_client.search(
    #         index="traceabilities_v1",
    #         body={
    #             "query": {
    #                 "bool": {
    #                     "should": [
    #                         {
    #                             "bool": {
    #                                 "must": [
    #                                     {"term": {"model_type.keyword": "App\\Models\\Nameplate"}},
    #                                     *(
    #                                         [{"term": {"model.flag.keyword": query.production_order_flag}}]
    #                                         if getattr(query, "production_order_flag", None) else []
    #                                     ),
    #                                     *(
    #                                         [{"term": {"model.production_order_id": query.production_order_id}}]
    #                                         if getattr(query, "production_order_id", None) else []
    #                                     )
    #                                 ]
    #                             }
    #                         },
    #                         {
    #                             "bool": {
    #                                 "must": [
    #                                     {"term": {"model_type.keyword": "App\\Models\\ProductionOrder"}},
    #                                     *(
    #                                         [{"term": {"model.id": query.production_order_id}}]
    #                                         if getattr(query, "production_order_id", None) else []
    #                                     )
    #                                 ]
    #                             }
    #                         }
    #                     ],
    #                     "minimum_should_match": 1
    #                 }
    #             },
    #             "sort": [{"id": {"order": "desc"}}],
    #             "size": query.size or 100
    #         }
    #     )

    #     return {
    #         "total": result["hits"]["total"]["value"],
    #         "data": [hit["_source"] for hit in result["hits"]["hits"]]
    #     }
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
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

# Search production_orders by shift-id
@api_router.get("/elasticsearch/search/production-orders/by-shift/{shift_id}")
async def search_by_shift(shift_id: int):
    try:
        result = await es_client.search(
            index="production_orders_v1",
            body={
                "query": {
                    "term": {
                        "shift_id": shift_id
                    }
                }
            }
        )
        
        # return {
        #     "total": result["hits"]["total"]["value"],
        #     "data": [hit["_source"] for hit in result["hits"]["hits"]]
        # }

        return [hit["_source"] for hit in result["hits"]["hits"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Search Endpoints
@api_router.post("/elasticsearch/production-orders/active")
async def production_orders_active(query: ProductionOrderActive):
    try:
        planning_dates = query.planning_dates

        if isinstance(planning_dates, list) and len(planning_dates) > 0:
            planning_dates_sorted = sorted(planning_dates)
            start_date = planning_dates_sorted[0]
            end_date = planning_dates_sorted[-1]
        elif isinstance(planning_dates, str):
            start_date = end_date = planning_dates
        else:
            raise HTTPException(status_code=400, detail="planning_dates harus string atau list tanggal")

        must_query = [
            # ✅ Filter shift_id
            {"term": {"shift_id": query.shift_id}},

            # ✅ Filter planning_date (range Y-m-d)
            {
                "range": {
                    "planning_date": {
                        "gte": start_date,
                        "lte": end_date,
                        "format": "yyyy-MM-dd"
                    }
                }
            }
        ]

        # ✅ Filter crew.user_id (nested field)
        if getattr(query, "user_id", None):
            must_query.append({
                "nested": {
                    "path": "crews",
                    "query": {"term": {"crews.user_id": query.user_id}}
                }
            })

        result = await es_client.search(
            index="production_orders_v1",
            body={
                "query": {
                    "bool": {
                        "must": must_query,
                        "filter": [
                            {
                                "terms": {
                                    "status.flag.keyword": ["ORDER_NEW", "ORDER_PROGRESS"]
                                }
                            }
                        ]
                    }
                },
                "sort": [{"id": {"order": "asc"}}],
                "size": query.size
            }
        )

        # ✅ Filter product_work_center.work_center.current_station.flag (nested field)
        if getattr(query, "station_flag", None):
            production_orders = []
            for hit in result["hits"]["hits"]:
                src = hit["_source"]

                # ✅ kalau ada product_work_center & current_station
                work_center = (
                    src.get("product_work_center", {})
                    .get("work_center", {})
                )

                if "current_station" in work_center and isinstance(work_center["current_station"], list):
                    # Filter manual di Python
                    filtered_station = [
                        s for s in work_center["current_station"]
                        if s.get("flag") == query.station_flag
                    ]
                    work_center["current_station"] = filtered_station

                production_orders.append(src)
            
            result = production_orders
        else:
            result = [hit["_source"] for hit in result["hits"]["hits"]]

        return result

        # return {
        #     "total": result["hits"]["total"]["value"],
        #     "data": [hit["_source"] for hit in result["hits"]["hits"]]
        # }
        # return [hit["_source"] for hit in result["hits"]["hits"]]

        # 🔧 Filter hasil agar current_station hanya berisi yang match inner_hits
        # production_orders = []
        # for hit in result["hits"]["hits"]:
        #     source = hit["_source"]
            
        #     # Ambil hasil inner_hits (kalau ada)
        #     inner_hits = (
        #         hit.get("inner_hits", {})
        #             .get("filtered_current_station", {})
        #             .get("hits", {})
        #             .get("hits", [])
        #     )

        #     # Kalau inner_hits ada, masukkan ke current_station
        #     if inner_hits:
        #         current_stations = [i["_source"] for i in inner_hits]
        #         if "product_work_center" in source and "work_center" in source["product_work_center"]:
        #             source["product_work_center"]["work_center"]["current_station"] = current_stations

        #     production_orders.append(source)

        # return production_orders
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

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # --- startup logic ---
#     print("🚀 Starting up FastAPI...")
    
#     yield  # <<< di sini app berjalan
    
#     # --- shutdown logic ---
#     print("🛑 Shutting down...")
#     client.close()
#     await es_client.close()

# app = FastAPI(lifespan=lifespan)