"""
Source Control - Git инструменты для управления версиями проекта
"""

import json
import os
from typing import Any, Dict, List, Optional

from ..base import Tool, ToolResult, ToolContext
from ._git import (
    find_git_root,
    get_git_status,
    get_git_diff,
    get_git_log,
    git_commit
)


class GitStatusTool(Tool):
    """Получение статуса Git репозитория"""
    
    name = "git_status"
    description = "Получает статус Git репозитория: ветка, изменённые файлы, неотслеживаемые файлы"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        repo_path = args.get("repo_path")
        
        if not repo_path:
            git_root = find_git_root(ctx.project_path)
            if not git_root:
                return ToolResult(
                    success=False,
                    error="Git репозиторий не найден",
                    message="Текущая директория не является Git репозиторием"
                )
            repo_path = str(git_root)
        
        try:
            result = get_git_status(repo_path)
            
            if result.get("success"):
                return ToolResult(
                    success=True,
                    data=result,
                    message=f"Ветка: {result.get('branch')}, изменений: {result.get('total_changes', 0)}"
                )
            else:
                return ToolResult(
                    success=False,
                    error=result.get("error", "Неизвестная ошибка"),
                    message="Ошибка получения статуса Git"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"Ошибка: {e}"
            )


class GitDiffTool(Tool):
    """Получение diff изменений"""
    
    name = "git_diff"
    description = "Получает diff для указанных файлов или всех изменённых файлов"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Список путей к файлам (опционально)"
            },
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        paths = args.get("paths")
        repo_path = args.get("repo_path")
        
        if not repo_path:
            git_root = find_git_root(ctx.project_path)
            if not git_root:
                return ToolResult(
                    success=False,
                    error="Git репозиторий не найден",
                    message="Текущая директория не является Git репозиторием"
                )
            repo_path = str(git_root)
        
        try:
            result = get_git_diff(repo_path, paths)
            
            if result.get("success"):
                stat = result.get("stat", "")
                lines_count = len(stat.split("\n")) if stat else 0
                
                return ToolResult(
                    success=True,
                    data=result,
                    message=f"Diff получен, строк в статистике: {lines_count}"
                )
            else:
                return ToolResult(
                    success=False,
                    error=result.get("error", "Неизвестная ошибка"),
                    message="Ошибка получения diff"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"Ошибка: {e}"
            )


class GitLogTool(Tool):
    """Получение истории коммитов"""
    
    name = "git_log"
    description = "Получает историю коммитов репозитория"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "max_count": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "description": "Максимальное количество коммитов",
                "default": 10
            },
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        max_count = args.get("max_count", 10)
        repo_path = args.get("repo_path")
        
        if not repo_path:
            git_root = find_git_root(ctx.project_path)
            if not git_root:
                return ToolResult(
                    success=False,
                    error="Git репозиторий не найден",
                    message="Текущая директория не является Git репозиторием"
                )
            repo_path = str(git_root)
        
        try:
            result = get_git_log(repo_path, max_count)
            
            if result.get("success"):
                commits = result.get("commits", [])
                return ToolResult(
                    success=True,
                    data=result,
                    message=f"Получено {len(commits)} коммитов"
                )
            else:
                return ToolResult(
                    success=False,
                    error=result.get("error", "Неизвестная ошибка"),
                    message="Ошибка получения истории коммитов"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"Ошибка: {e}"
            )


class GitCommitTool(Tool):
    """Создание коммита с указанными файлами"""
    
    name = "git_commit"
    description = "Создаёт новый коммит с явно указанными файлами (без git add all)"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Сообщение коммита"
            },
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Список путей к файлам для коммита (обязательно)"
            },
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        },
        "required": ["message", "paths"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        message = args.get("message")
        paths = args.get("paths", [])
        repo_path = args.get("repo_path")
        
        if not paths:
            return ToolResult(
                success=False,
                error="Не указаны файлы для коммита",
                message="Передайте список файлов в параметре paths"
            )
        
        if not repo_path:
            git_root = find_git_root(ctx.project_path)
            if not git_root:
                return ToolResult(
                    success=False,
                    error="Git репозиторий не найден",
                    message="Текущая директория не является Git репозиторием"
                )
            repo_path = str(git_root)
        
        try:
            result = git_commit(repo_path, message, paths)
            
            if result.get("success"):
                return ToolResult(
                    success=True,
                    data=result,
                    message=f"Коммит создан: {result.get('commit_hash', 'unknown')[:8]}"
                )
            else:
                return ToolResult(
                    success=False,
                    error=result.get("error", "Неизвестная ошибка"),
                    message="Ошибка создания коммита"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"Ошибка: {e}"
            )
