"""
Supabase API wrapper that mimics SQLAlchemy interface.
This allows the app to work with both SQLite (SQLAlchemy) and Supabase (API).
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from supabase import create_client, Client

import config

logger = logging.getLogger(__name__)


class SupabaseSession:
    """
    Wrapper around Supabase client that mimics SQLAlchemy session interface.
    """
    
    def __init__(self, client: Client):
        self.client = client
        self._closed = False
    
    def query(self, model_class):
        """Start a query for a model."""
        return SupabaseQuery(self.client, model_class)
    
    def add(self, obj):
        """Add an object to be inserted."""
        obj._session = self
        obj._pending_insert = True
    
    def commit(self):
        """Commit changes (no-op for Supabase, changes are immediate)."""
        pass
    
    def rollback(self):
        """Rollback changes (no-op for Supabase)."""
        pass
    
    def close(self):
        """Close the session."""
        self._closed = True
    
    def flush(self):
        """Flush changes (no-op for Supabase)."""
        pass


class SupabaseQuery:
    """Mimics SQLAlchemy Query interface for Supabase."""
    
    def __init__(self, client: Client, model_class):
        self.client = client
        self.model_class = model_class
        self.table_name = model_class.__tablename__
        self._filters = []
        self._limit_value = None
        self._offset_value = None
        self._order_by_cols = []
    
    def filter_by(self, **kwargs):
        """Filter by equality."""
        for key, value in kwargs.items():
            self._filters.append(('eq', key, value))
        return self
    
    def filter(self, *args):
        """Filter with expressions (simplified)."""
        # For now, just return self - advanced filters not implemented
        return self
    
    def order_by(self, *args):
        """Order results."""
        # Simplified - store column names
        for arg in args:
            if hasattr(arg, 'key'):
                self._order_by_cols.append(arg.key)
        return self
    
    def limit(self, value):
        """Limit results."""
        self._limit_value = value
        return self
    
    def offset(self, value):
        """Offset results."""
        self._offset_value = value
        return self
    
    def all(self) -> List:
        """Get all results."""
        query = self.client.table(self.table_name).select('*')
        
        # Apply filters
        for filter_type, key, value in self._filters:
            if filter_type == 'eq':
                query = query.eq(key, value)
        
        # Apply ordering
        if self._order_by_cols:
            for col in self._order_by_cols:
                query = query.order(col)
        
        # Apply limit/offset
        if self._limit_value:
            query = query.limit(self._limit_value)
        if self._offset_value:
            query = query.offset(self._offset_value)
        
        result = query.execute()
        return [self.model_class.from_dict(row) for row in result.data]
    
    def first(self) -> Optional[Any]:
        """Get first result."""
        results = self.limit(1).all()
        return results[0] if results else None
    
    def count(self) -> int:
        """Count results."""
        query = self.client.table(self.table_name).select('id', count='exact')
        
        # Apply filters
        for filter_type, key, value in self._filters:
            if filter_type == 'eq':
                query = query.eq(key, value)
        
        result = query.execute()
        return result.count if hasattr(result, 'count') else len(result.data)
    
    def delete(self):
        """Delete matching records."""
        # Get IDs first
        records = self.all()
        for record in records:
            self.client.table(self.table_name).delete().eq('id', record.id).execute()
        return len(records)


class SupabaseModel:
    """Base class for models that work with both SQLAlchemy and Supabase."""
    
    __tablename__ = None
    
    def __init__(self, **kwargs):
        self._session = None
        self._pending_insert = False
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SupabaseModel':
        """Create model instance from dictionary."""
        instance = cls()
        for key, value in data.items():
            # Handle datetime fields
            if key in ['published_date', 'fetched_date', 'received_date'] and value:
                if isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        pass
            setattr(instance, key, value)
        return instance
    
    def to_dict(self) -> Dict:
        """Convert model to dictionary for Supabase."""
        data = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            # Handle datetime fields
            if isinstance(value, datetime):
                value = value.isoformat()
            # Skip None values for optional fields
            if value is not None:
                data[key] = value
        return data
    
    def save(self, session: SupabaseSession):
        """Save to Supabase."""
        if not hasattr(self, 'id') or self.id is None:
            # Insert
            data = self.to_dict()
            data.pop('id', None)  # Remove id for insert
            result = session.client.table(self.__tablename__).insert(data).execute()
            if result.data:
                self.id = result.data[0]['id']
        else:
            # Update
            data = self.to_dict()
            session.client.table(self.__tablename__).update(data).eq('id', self.id).execute()


def get_supabase_client() -> Client:
    """Get Supabase client."""
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def get_supabase_session() -> SupabaseSession:
    """Get a Supabase session (wrapper)."""
    client = get_supabase_client()
    return SupabaseSession(client)

