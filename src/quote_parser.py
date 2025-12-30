"""Quote parser for CSV and JSON files with auto-detection."""

import csv
import json
import os
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass


@dataclass
class Quote:
    """Represents a quote with metadata."""
    text: str
    author: str
    source: Optional[str] = None


class QuoteParser:
    """Parser for CSV and JSON quote files."""

    # Common field name variations
    QUOTE_FIELDS = ['quote', 'text', 'quotation', 'q']
    AUTHOR_FIELDS = ['author', 'person', 'speaker', 'who', 'by']
    SOURCE_FIELDS = ['source', 'media', 'from', 'work', 'book', 'movie', 'show', 'occupation', 'role', 'title', 'position']

    @staticmethod
    def detect_file_type(filepath: str) -> str:
        """Detect if file is CSV or JSON."""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.csv':
            return 'csv'
        elif ext == '.json':
            return 'json'
        else:
            # Try to detect by content
            with open(filepath, 'r', encoding='utf-8') as f:
                first_char = f.read(1)
                if first_char == '[' or first_char == '{':
                    return 'json'
                else:
                    return 'csv'

    @staticmethod
    def normalize_field_name(field: str) -> Optional[str]:
        """Normalize field name to standard format."""
        field_lower = field.lower().strip()
        
        if field_lower in QuoteParser.QUOTE_FIELDS:
            return 'quote'
        elif field_lower in QuoteParser.AUTHOR_FIELDS:
            return 'author'
        elif field_lower in QuoteParser.SOURCE_FIELDS:
            return 'source'
        
        return None

    @classmethod
    def parse_csv(cls, filepath: str) -> Iterator[Quote]:
        """Parse CSV file and yield Quote objects."""
        with open(filepath, 'r', encoding='utf-8') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Map field names to standard names
            field_mapping = {}
            for field in reader.fieldnames:
                normalized = cls.normalize_field_name(field)
                if normalized:
                    field_mapping[normalized] = field
            
            # Process rows
            for row in reader:
                quote_text = None
                author_text = None
                source_text = None
                
                if 'quote' in field_mapping:
                    quote_text = row.get(field_mapping['quote'], '').strip()
                if 'author' in field_mapping:
                    author_text = row.get(field_mapping['author'], '').strip()
                if 'source' in field_mapping:
                    source_text = row.get(field_mapping['source'], '').strip()
                
                # If no mapping found, try direct access
                if not quote_text:
                    for field in cls.QUOTE_FIELDS:
                        if field in row and row[field].strip():
                            quote_text = row[field].strip()
                            break
                
                if not author_text:
                    for field in cls.AUTHOR_FIELDS:
                        if field in row and row[field].strip():
                            author_text = row[field].strip()
                            break
                
                if not source_text:
                    for field in cls.SOURCE_FIELDS:
                        if field in row and row[field].strip():
                            source_text = row[field].strip()
                            break
                
                if quote_text and author_text:
                    yield Quote(
                        text=quote_text,
                        author=author_text,
                        source=source_text if source_text else None
                    )

    @classmethod
    def parse_json(cls, filepath: str) -> Iterator[Quote]:
        """Parse JSON file and yield Quote objects."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle both list and single object
            if isinstance(data, dict):
                data = [data]
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                quote_text = None
                author_text = None
                source_text = None
                
                # Try to find quote field
                for field in cls.QUOTE_FIELDS:
                    if field in item and item[field]:
                        quote_text = str(item[field]).strip()
                        break
                
                # Try to find author field
                for field in cls.AUTHOR_FIELDS:
                    if field in item and item[field]:
                        author_text = str(item[field]).strip()
                        break
                
                # Try to find source field
                for field in cls.SOURCE_FIELDS:
                    if field in item and item[field]:
                        source_text = str(item[field]).strip()
                        break
                
                if quote_text and author_text:
                    yield Quote(
                        text=quote_text,
                        author=author_text,
                        source=source_text if source_text else None
                    )

    @classmethod
    def parse_file(cls, filepath: str) -> List[Quote]:
        """Parse a file (CSV or JSON) and return list of Quote objects."""
        file_type = cls.detect_file_type(filepath)
        
        if file_type == 'csv':
            return list(cls.parse_csv(filepath))
        elif file_type == 'json':
            return list(cls.parse_json(filepath))
        else:
            raise ValueError(f"Unsupported file type: {filepath}")

