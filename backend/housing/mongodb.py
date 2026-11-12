"""
MongoDB Atlas Client & Collection Helper for Nestora.
Connects to MongoDB Atlas using MONGODB_URI configured in settings or environment.
"""

import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_mongo_client = None


def get_mongo_uri():
    """Retrieve MongoDB URI from Django settings or environment variables."""
    return getattr(
        settings,
        'MONGODB_URI',
        os.getenv('MONGODB_URI', '')
    ).strip()


def get_mongo_db_name():
    """Retrieve MongoDB database name (default: 'nestora')."""
    return getattr(
        settings,
        'MONGODB_DB_NAME',
        os.getenv('MONGODB_DB_NAME', 'nestora')
    ).strip() or 'nestora'


def get_mongo_client(max_pool_size=50, timeout_ms=5000):
    """
    Get or initialize a thread-safe MongoClient instance.
    Returns None if MONGODB_URI is not configured.
    """
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client

    uri = get_mongo_uri()
    if not uri:
        logger.warning("MONGODB_URI is not set. MongoDB Atlas features are disabled.")
        return None

    try:
        from pymongo import MongoClient
        _mongo_client = MongoClient(
            uri,
            maxPoolSize=max_pool_size,
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=timeout_ms,
            appname="NestoraDjango"
        )
        return _mongo_client
    except Exception as exc:
        logger.error(f"Failed to initialize MongoClient: {exc}")
        return None


def get_mongo_db():
    """
    Get the MongoDB Database object for 'nestora'.
    Returns None if client is unavailable.
    """
    client = get_mongo_client()
    if client is None:
        return None
    db_name = get_mongo_db_name()
    return client[db_name]


def get_collections():
    """
    Return a dictionary of standard Nestora collections.
    Returns None if connection is unavailable.
    """
    db = get_mongo_db()
    if db is None:
        return None

    return {
        'hostels': db['hostels'],
        'rooms': db['rooms'],
        'beds': db['beds'],
        'students': db['students'],
        'roommate_profiles': db['roommate_profiles'],
        'applications': db['applications'],
        'allocation_runs': db['allocation_runs'],
        'allocation_records': db['allocation_records'],
        'audit_logs': db['audit_logs'],
    }


def test_connection():
    """
    Test connectivity to MongoDB Atlas.
    Returns (True, message) on success or (False, error_message).
    """
    uri = get_mongo_uri()
    if not uri:
        return (False, "MONGODB_URI is not configured in environment or settings.")

    try:
        from pymongo import MongoClient
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        res = client.admin.command('ping')
        db_name = get_mongo_db_name()
        db = client[db_name]
        collections = db.list_collection_names()
        return (True, f"Connected to MongoDB Atlas! Database: '{db_name}', Collections: {len(collections)}")
    except Exception as exc:
        return (False, f"MongoDB Atlas connection failed: {exc}")
