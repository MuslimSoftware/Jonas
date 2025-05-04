# Helper functions for database agent tools
import logging
import json
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from decimal import Decimal
from datetime import datetime
from pymongo.errors import PyMongoError
from bson import ObjectId

# Assuming these functions correctly retrieve the necessary objects
from app.infrastructure.database.external import get_external_mongo_db, get_sql_engine

logger = logging.getLogger(__name__) # Use a logger specific to helpers

# --- SQL Execution Helper --- 

def execute_sql_query_with_engine(sql_engine: Engine, query: str) -> Dict[str, Any]:
    """Executes a read-only SQL query and returns the result as a dictionary."""
    if sql_engine is None:
        # This check might be redundant if get_sql_engine handles it, but good safety
        logger.error("Helper: SQL Engine is None, cannot execute query.")
        # Return dict directly
        return {"status": "error", "message": "Database engine is not initialized."}

    logger.info(f"Helper (SQL): Attempting to execute query: '{query[:100]}...'")

    try:
        with sql_engine.connect() as connection:
            result_proxy = connection.execute(text(query))
            results = result_proxy.mappings().all()
            
            # Convert RowMapping to plain dicts & handle special types
            plain_results = []
            for row in results:
                plain_row = {}
                for key, value in row.items():
                    if isinstance(value, Decimal):
                        plain_row[key] = float(value) 
                    elif isinstance(value, datetime):
                        plain_row[key] = value.isoformat()
                    else:
                        plain_row[key] = value
                plain_results.append(plain_row)
                
            logger.info(f"Helper (SQL): Query executed successfully. Rows returned: {len(plain_results)}")
            # Return dict directly
            return {"status": "success", "result": plain_results}

    except SQLAlchemyError as e:
        logger.error(f"Helper (SQL): SQLAlchemy Error executing query: {e}", exc_info=True)
        error_code = getattr(e.orig, 'errno', 'N/A')
        error_msg = getattr(e.orig, 'msg', str(e))
        # Return dict directly
        return {"status": "error", "message": f"Database query failed (Code: {error_code}, Msg: {error_msg})"}
    except Exception as e:
        logger.error(f"Helper (SQL): Non-SQLAlchemy error during query execution: {e}", exc_info=True)
        # Return dict directly
        return {"status": "error", "message": f"An unexpected error occurred during database query execution."}

# --- MongoDB Execution Helpers --- 

def _default_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj) # Or str(obj) if precision is critical
    raise TypeError ("Type %s not serializable" % type(obj))

def execute_mongo_query(query_dict: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
    """Executes a MongoDB query and returns the result as a dictionary."""
    db = get_external_mongo_db()
    if db is None:
        logger.error("Helper (Mongo): MongoDB is None, cannot execute query.")
        # Return dict directly
        return {"status": "error", "error_message": "External MongoDB database is not initialized or configured."}

    collection_name = "debug_logs" # Hardcode collection name
    logger.info(f"Helper (Mongo): Attempting query on '{collection_name}': {query_dict}, limit: {limit}")

    try:
        mongo_collection = db[collection_name]
        cursor = mongo_collection.find(query_dict).limit(limit)
        results = list(cursor)
        
        # Serialize results 
        serializable_results = json.dumps(results, default=_default_serializer)
        # Parse back to ensure it's valid list for the final structure
        parsed_results: List[Dict[str, Any]] = json.loads(serializable_results) 

        logger.info(f"Helper (Mongo): Query executed successfully. Documents returned: {len(parsed_results)}")
        # Return dict directly
        return {"status": "success", "data": parsed_results}

    except PyMongoError as e:
        logger.error(f"Helper (Mongo): PyMongo Error executing query on '{collection_name}': {e}", exc_info=True)
        # Return dict directly
        return {"status": "error", "error_message": f"MongoDB query failed: {e}"}
    except Exception as e:
        logger.error(f"Helper (Mongo): Non-PyMongo error during query execution: {e}", exc_info=True)
        # Return dict directly
        return {"status": "error", "error_message": "An unexpected error occurred during MongoDB query execution."}
