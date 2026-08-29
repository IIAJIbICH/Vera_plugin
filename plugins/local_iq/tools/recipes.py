"""
Local IQ - Сохранение и поиск рецептов (последовательностей шагов)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from ..base import Tool, ToolResult, ToolContext


class RecipeStore:
    """JSONL-хранилище рецептов"""
    
    def __init__(self, plugin_path: str):
        self.storage_path = Path(plugin_path) / "recipes.jsonl"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _read_all(self) -> List[Dict[str, Any]]:
        """Читает все рецепты из файла"""
        recipes = []
        
        if not self.storage_path.exists():
            return recipes
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            recipes.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
        
        return recipes
    
    def _write_all(self, recipes: List[Dict[str, Any]]) -> None:
        """Записывает все рецепты в файл"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                for recipe in recipes:
                    f.write(json.dumps(recipe, ensure_ascii=False) + '\n')
        except Exception as e:
            raise Exception(f"Ошибка записи хранилища: {e}")
    
    def add(self, task: str, steps: List[str], 
            category: Optional[str] = None,
            notes: Optional[str] = None) -> Dict[str, Any]:
        """Добавляет новый рецепт"""
        recipe = {
            "id": str(uuid.uuid4()),
            "task": task,
            "steps": steps,
            "category": category or "general",
            "notes": notes or "",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        recipes = self._read_all()
        recipes.append(recipe)
        self._write_all(recipes)
        
        return recipe
    
    def search(self, task_query: str, category: Optional[str] = None,
               limit: int = 5) -> List[Dict[str, Any]]:
        """Ищет рецепты по задаче"""
        recipes = self._read_all()
        results = []
        query_lower = task_query.lower()
        
        for recipe in recipes:
            # Фильтр по категории
            if category and recipe.get("category") != category:
                continue
            
            # Поиск по задаче и шагам
            task_match = query_lower in recipe.get("task", "").lower()
            steps_match = any(query_lower in step.lower() for step in recipe.get("steps", []))
            
            if task_match or steps_match:
                results.append(recipe)
                
                if len(results) >= limit:
                    break
        
        return results


class SaveRecipeTool(Tool):
    """Сохранение рецепта"""
    
    name = "save_recipe"
    description = "Сохраняет последовательность шагов (рецепт) для решения задачи"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Описание задачи"
            },
            "steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Список шагов выполнения"
            },
            "category": {
                "type": "string",
                "description": "Категория рецепта",
                "default": "general"
            },
            "notes": {
                "type": "string",
                "description": "Дополнительные заметки"
            }
        },
        "required": ["task", "steps"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        task = args.get("task")
        steps = args.get("steps", [])
        category = args.get("category", "general")
        notes = args.get("notes", "")
        
        if not task:
            return ToolResult(
                success=False,
                error="Не указана задача",
                message="Передайте параметр task"
            )
        
        if not steps:
            return ToolResult(
                success=False,
                error="Не указаны шаги",
                message="Передайте параметр steps"
            )
        
        store = RecipeStore(ctx.plugin_path)
        
        try:
            recipe = store.add(task, steps, category, notes)
            
            return ToolResult(
                success=True,
                data={
                    "id": recipe["id"],
                    "task": recipe["task"],
                    "steps_count": len(recipe["steps"]),
                    "category": recipe["category"]
                },
                message=f"Рецепт '{task}' сохранен с {len(steps)} шагами"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Ошибка сохранения рецепта"
            )


class FindRecipeTool(Tool):
    """Поиск рецепта"""
    
    name = "find_recipe"
    description = "Ищет рецепт по задаче или названию"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "task_query": {
                "type": "string",
                "description": "Поисковый запрос по задаче"
            },
            "category": {
                "type": "string",
                "description": "Фильтр по категории"
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "description": "Максимум результатов",
                "default": 5
            }
        },
        "required": ["task_query"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        task_query = args.get("task_query")
        category = args.get("category")
        limit = args.get("limit", 5)
        
        if not task_query:
            return ToolResult(
                success=False,
                error="Не указан поисковый запрос",
                message="Передайте параметр task_query"
            )
        
        store = RecipeStore(ctx.plugin_path)
        
        try:
            results = store.search(task_query, category, limit)
            
            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "count": len(results),
                    "query": task_query
                },
                message=f"Найдено {len(results)} рецептов по запросу '{task_query}'"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Ошибка поиска рецептов"
            )
