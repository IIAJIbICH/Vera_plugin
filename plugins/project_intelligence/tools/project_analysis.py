"""
Project Intelligence - Анализ проекта Unreal Engine без редактора
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import Tool, ToolResult, ToolContext


def find_uproject_file(project_path: str) -> Optional[Path]:
    """Находит файл .uproject в проекте"""
    path = Path(project_path)
    
    # Ищем в корневой директории
    for uproject in path.glob("*.uproject"):
        return uproject
    
    return None


def analyze_uproject(uproject_path: str) -> Dict[str, Any]:
    """Анализирует файл .uproject"""
    try:
        with open(uproject_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result = {
            "project_name": data.get("Name", "Unknown"),
            "engine_version": data.get("EngineAssociation", "Unknown"),
            "description": data.get("Description", ""),
            "plugins": [],
            "categories": data.get("Categories", [])
        }
        
        # Анализируем плагины
        plugins = data.get("Plugins", [])
        for plugin in plugins:
            result["plugins"].append({
                "name": plugin.get("Name", "Unknown"),
                "enabled": plugin.get("Enabled", True)
            })
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def count_assets(content_path: str) -> Dict[str, int]:
    """Подсчитывает количество активов разных типов"""
    counts = {
        "uasset": 0,
        "umap": 0,
        "uexp": 0,
        "total": 0
    }
    
    content_dir = Path(content_path)
    if not content_dir.exists():
        return counts
    
    for ext in ["*.uasset", "*.umap", "*.uexp"]:
        files = list(content_dir.rglob(ext))
        key = ext[1:]  # убираем точку
        counts[key] = len(files)
        if ext != "*.uexp":
            counts["total"] += len(files)
    
    return counts


def find_assets_by_name(content_path: str, name: str, extensions: List[str]) -> List[Dict[str, Any]]:
    """Ищет активы по имени"""
    results = []
    content_dir = Path(content_path)
    
    if not content_dir.exists():
        return results
    
    name_lower = name.lower()
    
    for ext in extensions:
        pattern = f"*{ext}"
        for file_path in content_dir.rglob(pattern):
            if name_lower in file_path.name.lower():
                try:
                    file_size = file_path.stat().st_size
                except:
                    file_size = 0
                
                relative_path = str(file_path.relative_to(content_dir))
                
                results.append({
                    "path": str(file_path),
                    "relative_path": relative_path,
                    "name": file_path.stem,
                    "extension": file_path.suffix,
                    "size_bytes": file_size
                })
    
    return sorted(results, key=lambda x: x["size_bytes"], reverse=True)


class AnalyzeProjectTool(Tool):
    """Анализ проекта Unreal Engine"""
    
    name = "analyze_project"
    description = "Анализирует проект Unreal Engine: читает .uproject, плагины, подсчитывает активы"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Путь к проекту (по умолчанию используется текущий проект)"
            },
            "include_assets": {
                "type": "boolean",
                "description": "Включить анализ активов",
                "default": False
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        project_path = args.get("project_path", ctx.project_path)
        include_assets = args.get("include_assets", False)
        
        # Находим .uproject файл
        uproject = find_uproject_file(project_path)
        if not uproject:
            return ToolResult(
                success=False,
                error="Файл .uproject не найден",
                message=f"В директории {project_path} не найден файл .uproject"
            )
        
        # Анализируем .uproject
        project_info = analyze_uproject(str(uproject))
        
        if not project_info.get("success"):
            return ToolResult(
                success=False,
                error=project_info.get("error", "Неизвестная ошибка"),
                message="Ошибка анализа .uproject"
            )
        
        # Подсчитываем активы если требуется
        content_path = os.path.join(project_path, "Content")
        if include_assets and os.path.exists(content_path):
            asset_counts = count_assets(content_path)
            project_info["asset_count"] = asset_counts["uasset"]
            project_info["map_count"] = asset_counts["umap"]
            project_info["total_files"] = asset_counts["total"]
        
        # Убираем technical fields из ответа
        response_data = {
            "project_name": project_info.get("project_name"),
            "engine_version": project_info.get("engine_version"),
            "description": project_info.get("description"),
            "plugins": project_info.get("plugins", []),
            "categories": project_info.get("categories", [])
        }
        
        if include_assets:
            response_data["asset_count"] = project_info.get("asset_count", 0)
            response_data["map_count"] = project_info.get("map_count", 0)
        
        plugins_count = len(project_info.get("plugins", []))
        
        return ToolResult(
            success=True,
            data=response_data,
            message=f"Проект '{project_info.get('project_name')}' проанализирован, плагинов: {plugins_count}"
        )


class FindAssetTool(Tool):
    """Поиск активов по имени"""
    
    name = "find_asset"
    description = "Ищет файлы активов (.uasset, .umap) по имени или части имени"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Имя или часть имени для поиска"
            },
            "extensions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Расширения для поиска",
                "default": [".uasset", ".umap"]
            },
            "project_path": {
                "type": "string",
                "description": "Путь к проекту (по умолчанию используется текущий проект)"
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000,
                "description": "Максимальное количество результатов",
                "default": 100
            }
        },
        "required": ["name"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        name = args.get("name")
        extensions = args.get("extensions", [".uasset", ".umap"])
        project_path = args.get("project_path", ctx.project_path)
        limit = args.get("limit", 100)
        
        if not name:
            return ToolResult(
                success=False,
                error="Не указано имя для поиска",
                message="Передайте параметр name для поиска активов"
            )
        
        content_path = os.path.join(project_path, "Content")
        
        if not os.path.exists(content_path):
            return ToolResult(
                success=False,
                error="Директория Content не найдена",
                message=f"Путь {content_path} не существует"
            )
        
        # Ищем активы
        results = find_assets_by_name(content_path, name, extensions)
        
        # Ограничиваем количество результатов
        if len(results) > limit:
            results = results[:limit]
        
        return ToolResult(
            success=True,
            data={
                "results": results,
                "count": len(results),
                "query": name,
                "extensions": extensions
            },
            message=f"Найдено {len(results)} активов по запросу '{name}'"
        )
