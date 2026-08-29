"""
Memory - Сохранение и поиск воспоминаний в JSONL-хранилище
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from ..base import Tool, ToolResult, ToolContext


class MemoryStore:
    """JSONL-хранилище воспоминаний"""
    
    def __init__(self, plugin_path: str):
        self.storage_path = Path(plugin_path) / "memories.jsonl"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _read_all(self) -> List[Dict[str, Any]]:
        """Читает все воспоминания из файла"""
        memories = []
        
        if not self.storage_path.exists():
            return memories
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            memories.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
        
        return memories
    
    def _write_all(self, memories: List[Dict[str, Any]]) -> None:
        """Записывает все воспоминания в файл"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                for memory in memories:
                    f.write(json.dumps(memory, ensure_ascii=False) + '\n')
        except Exception as e:
            raise Exception(f"Ошибка записи хранилища: {e}")
    
    def add(self, content: str, category: Optional[str] = None, 
            tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Добавляет новое воспоминание"""
        memory = {
            "id": str(uuid.uuid4()),
            "content": content,
            "category": category or "general",
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        memories = self._read_all()
        memories.append(memory)
        self._write_all(memories)
        
        return memory
    
    def search(self, query: str, category: Optional[str] = None, 
               limit: int = 10) -> List[Dict[str, Any]]:
        """Ищет воспоминания по запросу"""
        memories = self._read_all()
        results = []
        query_lower = query.lower()
        
        for memory in memories:
            # Фильтр по категории
            if category and memory.get("category") != category:
                continue
            
            # Поиск по содержимому и тегам
            content_match = query_lower in memory.get("content", "").lower()
            tags_match = any(query_lower in tag.lower() for tag in memory.get("tags", []))
            
            if content_match or tags_match:
                results.append(memory)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def list_all(self, category: Optional[str] = None, 
                 limit: int = 50) -> List[Dict[str, Any]]:
        """Возвращает список всех воспоминаний"""
        memories = self._read_all()
        
        if category:
            memories = [m for m in memories if m.get("category") == category]
        
        # Сортируем по дате создания (новые первые)
        memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return memories[:limit]
    
    def delete(self, memory_id: str) -> bool:
        """Удаляет воспоминание по ID"""
        memories = self._read_all()
        original_count = len(memories)
        
        memories = [m for m in memories if m.get("id") != memory_id]
        
        if len(memories) < original_count:
            self._write_all(memories)
            return True
        
        return False
    
    def get_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Получает воспоминание по ID"""
        memories = self._read_all()
        
        for memory in memories:
            if memory.get("id") == memory_id:
                return memory
        
        return None


class RememberTool(Tool):
    """Сохранение воспоминания"""
    
    name = "remember"
    description = "Сохраняет факт/воспоминание в JSONL-хранилище"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "Содержание воспоминания"
            },
            "category": {
                "type": "string",
                "description": "Категория воспоминания",
                "default": "general"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Теги для поиска"
            }
        },
        "required": ["content"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        content = args.get("content")
        category = args.get("category", "general")
        tags = args.get("tags", [])
        
        if not content:
            return ToolResult(
                success=False,
                error="Не указано содержание воспоминания",
                message="Передайте параметр content"
            )
        
        store = MemoryStore(ctx.plugin_path)
        
        try:
            memory = store.add(content, category, tags)
            
            return ToolResult(
                success=True,
                data={
                    "id": memory["id"],
                    "created_at": memory["created_at"],
                    "content": memory["content"],
                    "category": memory["category"]
                },
                message=f"Воспоминание сохранено с ID: {memory['id'][:8]}..."
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Ошибка сохранения воспоминания"
            )


class RecallTool(Tool):
    """Поиск воспоминаний"""
    
    name = "recall"
    description = "Ищет воспоминания по запросу"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Поисковый запрос"
            },
            "category": {
                "type": "string",
                "description": "Фильтр по категории"
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "description": "Максимум результатов",
                "default": 10
            }
        },
        "required": ["query"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        query = args.get("query")
        category = args.get("category")
        limit = args.get("limit", 10)
        
        if not query:
            return ToolResult(
                success=False,
                error="Не указан поисковый запрос",
                message="Передайте параметр query"
            )
        
        store = MemoryStore(ctx.plugin_path)
        
        try:
            results = store.search(query, category, limit)
            
            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "count": len(results),
                    "query": query
                },
                message=f"Найдено {len(results)} воспоминаний по запросу '{query}'"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Ошибка поиска воспоминаний"
            )


class ListMemoriesTool(Tool):
    """Список всех воспоминаний"""
    
    name = "list_memories"
    description = "Возвращает список всех воспоминаний"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Фильтр по категории"
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 200,
                "description": "Максимум результатов",
                "default": 50
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        category = args.get("category")
        limit = args.get("limit", 50)
        
        store = MemoryStore(ctx.plugin_path)
        
        try:
            memories = store.list_all(category, limit)
            
            return ToolResult(
                success=True,
                data={
                    "memories": memories,
                    "total": len(memories)
                },
                message=f"Всего {len(memories)} воспоминаний"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Ошибка получения списка воспоминаний"
            )


class ForgetTool(Tool):
    """Удаление воспоминания"""
    
    name = "forget"
    description = "Удаляет воспоминание по ID"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "string",
                "description": "ID воспоминания для удаления"
            },
            "confirm": {
                "type": "boolean",
                "description": "Подтверждение удаления"
            }
        },
        "required": ["memory_id", "confirm"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        memory_id = args.get("memory_id")
        confirm = args.get("confirm", False)
        
        if not memory_id:
            return ToolResult(
                success=False,
                error="Не указан ID воспоминания",
                message="Передайте параметр memory_id"
            )
        
        if not confirm:
            return ToolResult(
                success=False,
                error="Требуется подтверждение",
                message="Передайте confirm=true для удаления"
            )
        
        store = MemoryStore(ctx.plugin_path)
        
        try:
            # Проверяем существование
            memory = store.get_by_id(memory_id)
            if not memory:
                return ToolResult(
                    success=False,
                    error="Воспоминание не найдено",
                    message=f"ID {memory_id} не существует"
                )
            
            deleted = store.delete(memory_id)
            
            if deleted:
                return ToolResult(
                    success=True,
                    data={
                        "deleted": True,
                        "memory_id": memory_id
                    },
                    message="Воспоминание удалено"
                )
            else:
                return ToolResult(
                    success=False,
                    error="Ошибка удаления",
                    message="Не удалось удалить воспоминание"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Ошибка удаления воспоминания"
            )
