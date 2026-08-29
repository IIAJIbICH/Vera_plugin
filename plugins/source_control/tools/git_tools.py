"""
Source Control - Git инструменты для управления версиями проекта
Расширенный набор: status, diff, log, commit, branch, stash, reset, pull, push
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
    git_commit,
    git_branch_list,
    git_branch_create,
    git_branch_checkout,
    git_branch_delete,
    git_stash_save,
    git_stash_list,
    git_stash_pop,
    git_stash_apply,
    git_resolve_conflict,
    git_reset_soft,
    git_reset_hard,
    git_pull,
    git_push
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


class GitBranchTool(Tool):
    """Управление ветками Git"""
    
    name = "git_branch"
    description = "Список, создание, переключение или удаление веток Git"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "create", "checkout", "delete"],
                "description": "Действие с веткой"
            },
            "name": {
                "type": "string",
                "description": "Имя ветки (для create/checkout/delete)"
            },
            "force": {
                "type": "boolean",
                "description": "Принудительное удаление (для delete)",
                "default": False
            },
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        },
        "required": ["action"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        action = args.get("action")
        name = args.get("name")
        force = args.get("force", False)
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
            if action == "list":
                result = git_branch_list(repo_path)
            elif action == "create":
                if not name:
                    return ToolResult(success=False, error="Не указано имя ветки")
                result = git_branch_create(repo_path, name)
            elif action == "checkout":
                if not name:
                    return ToolResult(success=False, error="Не указано имя ветки")
                result = git_branch_checkout(repo_path, name)
            elif action == "delete":
                if not name:
                    return ToolResult(success=False, error="Не указано имя ветки")
                result = git_branch_delete(repo_path, name, force)
            else:
                return ToolResult(success=False, error=f"Неизвестное действие: {action}")
            
            if result.get("success"):
                return ToolResult(success=True, data=result, message=result.get("message", "OK"))
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
                
        except Exception as e:
            return ToolResult(success=False, error=str(e), message=f"Ошибка: {e}")


class GitStashTool(Tool):
    """Управление stash Git"""
    
    name = "git_stash"
    description = "Сохранение, применение или извлечение изменений в stash"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["save", "list", "pop", "apply"],
                "description": "Действие со stash"
            },
            "message": {
                "type": "string",
                "description": "Сообщение для save"
            },
            "index": {
                "type": "integer",
                "description": "Индекс stash для pop/apply"
            },
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        },
        "required": ["action"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        action = args.get("action")
        message = args.get("message")
        index = args.get("index")
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
            if action == "save":
                result = git_stash_save(repo_path, message)
            elif action == "list":
                result = git_stash_list(repo_path)
            elif action == "pop":
                result = git_stash_pop(repo_path, index)
            elif action == "apply":
                result = git_stash_apply(repo_path, index)
            else:
                return ToolResult(success=False, error=f"Неизвестное действие: {action}")
            
            if result.get("success"):
                return ToolResult(success=True, data=result, message=result.get("message", "OK"))
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
                
        except Exception as e:
            return ToolResult(success=False, error=str(e), message=f"Ошибка: {e}")


class GitResolveConflictTool(Tool):
    """Разрешение конфликта слияния"""
    
    name = "git_resolve_conflict"
    description = "Отмечает файл как разрешённый после конфликта слияния"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Путь к файлу с разрешённым конфликтом"
            },
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        },
        "required": ["path"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        path = args.get("path")
        repo_path = args.get("repo_path")
        
        if not path:
            return ToolResult(success=False, error="Не указан путь к файлу")
        
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
            result = git_resolve_conflict(repo_path, path)
            
            if result.get("success"):
                return ToolResult(success=True, data=result, message=result.get("message", "OK"))
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
                
        except Exception as e:
            return ToolResult(success=False, error=str(e), message=f"Ошибка: {e}")


class GitResetTool(Tool):
    """Сброс Git до указанного коммита"""
    
    name = "git_reset"
    description = "Выполняет мягкий или жёсткий сброс до указанного коммита"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "Целевой коммит (hash, tag, branch)"
            },
            "mode": {
                "type": "string",
                "enum": ["soft", "hard"],
                "description": "Режим сброса: soft (сохраняет изменения) или hard (теряет)",
                "default": "soft"
            },
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        },
        "required": ["target"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        target = args.get("target")
        mode = args.get("mode", "soft")
        repo_path = args.get("repo_path")
        
        if not target:
            return ToolResult(success=False, error="Не указана целевая точка сброса")
        
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
            if mode == "soft":
                result = git_reset_soft(repo_path, target)
            else:
                result = git_reset_hard(repo_path, target)
            
            if result.get("success"):
                return ToolResult(success=True, data=result, message=result.get("message", "OK"))
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
                
        except Exception as e:
            return ToolResult(success=False, error=str(e), message=f"Ошибка: {e}")


class GitPullTool(Tool):
    """Pull изменений из удалённого репозитория"""
    
    name = "git_pull"
    description = "Получает изменения из удалённого репозитория"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "remote": {
                "type": "string",
                "description": "Имя удалённого репозитория",
                "default": "origin"
            },
            "branch": {
                "type": "string",
                "description": "Имя ветки (опционально)"
            },
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        remote = args.get("remote", "origin")
        branch = args.get("branch")
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
            result = git_pull(repo_path, remote, branch)
            
            if result.get("success"):
                return ToolResult(success=True, data=result, message="Изменения получены")
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
                
        except Exception as e:
            return ToolResult(success=False, error=str(e), message=f"Ошибка: {e}")


class GitPushTool(Tool):
    """Push изменений в удалённый репозиторий"""
    
    name = "git_push"
    description = "Отправляет изменения в удалённый репозиторий"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "remote": {
                "type": "string",
                "description": "Имя удалённого репозитория",
                "default": "origin"
            },
            "branch": {
                "type": "string",
                "description": "Имя ветки (опционально)"
            },
            "force": {
                "type": "boolean",
                "description": "Принудительная отправка",
                "default": False
            },
            "repo_path": {
                "type": "string",
                "description": "Путь к репозиторию (по умолчанию ищется от корня проекта)"
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        remote = args.get("remote", "origin")
        branch = args.get("branch")
        force = args.get("force", False)
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
            result = git_push(repo_path, remote, branch, force)
            
            if result.get("success"):
                return ToolResult(success=True, data=result, message="Изменения отправлены")
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
                
        except Exception as e:
            return ToolResult(success=False, error=str(e), message=f"Ошибка: {e}")
