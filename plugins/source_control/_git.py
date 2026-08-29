"""
Вспомогательный модуль для Git-операций
Используется плагином Source Control
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any


class GitError(Exception):
    """Ошибка выполнения Git-команды"""
    pass


def find_git_root(start_path: Optional[str] = None) -> Optional[Path]:
    """Находит корень Git репозитория"""
    if start_path is None:
        start_path = os.getcwd()
    
    current = Path(start_path)
    
    while current != current.parent:
        git_dir = current / ".git"
        if git_dir.exists():
            return current
        current = current.parent
    
    return None


def run_git_command(args: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
    """Выполняет Git команду и возвращает результат"""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Превышено время выполнения команды",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "returncode": -1
        }


def get_git_status(repo_path: str) -> Dict[str, Any]:
    """Получает статус Git репозитория"""
    result = run_git_command(["status", "--porcelain", "--branch"], cwd=repo_path)
    
    if not result["success"]:
        return result
    
    lines = result["stdout"].split("\n")
    branch_info = ""
    changed_files = []
    staged_files = []
    untracked_files = []
    
    for line in lines:
        if not line:
            continue
        
        if line.startswith("##"):
            branch_info = line[3:]
        elif line.startswith("??"):
            untracked_files.append(line[3:].strip())
        elif line.startswith(" A") or line.startswith("AM") or line.startswith("MM"):
            changed_files.append(line[3:].strip())
        elif line.startswith("A ") or line.startswith("M ") or line.startswith("D "):
            staged_files.append(line[3:].strip())
    
    return {
        "success": True,
        "branch": branch_info.split("...")[0] if branch_info else "unknown",
        "ahead_behind": branch_info.split("...")[1] if "..." in branch_info else "",
        "changed_files": changed_files,
        "staged_files": staged_files,
        "untracked_files": untracked_files,
        "total_changes": len(changed_files) + len(staged_files) + len(untracked_files)
    }


def get_git_diff(repo_path: str, paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Получает diff для указанных файлов"""
    args = ["diff", "--stat"]
    
    if paths:
        args.extend(["--"] + paths)
    
    result = run_git_command(args, cwd=repo_path)
    
    if not result["success"]:
        return result
    
    # Получаем полный diff
    full_diff_args = ["diff"]
    if paths:
        full_diff_args.extend(["--"] + paths)
    
    full_result = run_git_command(full_diff_args, cwd=repo_path)
    
    return {
        "success": True,
        "stat": result["stdout"],
        "diff": full_result["stdout"] if full_result["success"] else ""
    }


def get_git_log(repo_path: str, max_count: int = 10) -> Dict[str, Any]:
    """Получает историю коммитов"""
    format_str = "%H|%an|%ae|%ai|%s"
    result = run_git_command(
        ["log", f"-{max_count}", f"--pretty=format:{format_str}"],
        cwd=repo_path
    )
    
    if not result["success"]:
        return result
    
    commits = []
    for line in result["stdout"].split("\n"):
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) >= 5:
            commits.append({
                "hash": parts[0],
                "author_name": parts[1],
                "author_email": parts[2],
                "date": parts[3],
                "message": parts[4]
            })
    
    return {
        "success": True,
        "commits": commits,
        "count": len(commits)
    }


def git_commit(repo_path: str, message: str, paths: List[str]) -> Dict[str, Any]:
    """Создаёт коммит с указанными файлами"""
    if not paths:
        return {
            "success": False,
            "error": "Не указаны файлы для коммита"
        }
    
    # Добавляем только указанные файлы
    add_result = run_git_command(["add"] + paths, cwd=repo_path)
    
    if not add_result["success"]:
        return add_result
    
    # Создаём коммит
    commit_result = run_git_command(
        ["commit", "-m", message],
        cwd=repo_path
    )
    
    if not commit_result["success"]:
        # Отменяем add если коммит не удался
        run_git_command(["reset", "HEAD"] + paths, cwd=repo_path)
        return commit_result
    
    # Получаем hash коммита
    hash_result = run_git_command(["rev-parse", "HEAD"], cwd=repo_path)
    
    return {
        "success": True,
        "commit_hash": hash_result["stdout"] if hash_result["success"] else "unknown",
        "message": message,
        "files_count": len(paths)
    }


def git_branch_list(repo_path: str) -> Dict[str, Any]:
    """Получает список веток"""
    result = run_git_command(["branch", "-a"], cwd=repo_path)
    
    if not result["success"]:
        return result
    
    branches = []
    current = ""
    
    for line in result["stdout"].split("\n"):
        if not line:
            continue
        line = line.strip()
        if line.startswith("*"):
            current = line[2:].strip()
            branches.append(current)
        else:
            branches.append(line)
    
    return {
        "success": True,
        "branches": branches,
        "current": current
    }


def git_branch_create(repo_path: str, name: str) -> Dict[str, Any]:
    """Создаёт новую ветку"""
    result = run_git_command(["checkout", "-b", name], cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "branch": name,
        "message": f"Ветка {name} создана и переключена"
    }


def git_branch_checkout(repo_path: str, name: str) -> Dict[str, Any]:
    """Переключается на существующую ветку"""
    result = run_git_command(["checkout", name], cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "branch": name,
        "message": f"Переключено на ветку {name}"
    }


def git_branch_delete(repo_path: str, name: str, force: bool = False) -> Dict[str, Any]:
    """Удаляет ветку"""
    flag = "-D" if force else "-d"
    result = run_git_command(["branch", flag, name], cwd=repo_path)
    
    if not result["success"]:
        return {
            "success": False,
            "error": result.get("stderr", "Ошибка удаления ветки")
        }
    
    return {
        "success": True,
        "branch": name,
        "message": f"Ветка {name} удалена"
    }


def git_stash_save(repo_path: str, message: Optional[str] = None) -> Dict[str, Any]:
    """Сохраняет изменения в stash"""
    args = ["stash", "save"]
    if message:
        args.append(message)
    
    result = run_git_command(args, cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "message": message or "Stash saved",
        "output": result["stdout"]
    }


def git_stash_list(repo_path: str) -> Dict[str, Any]:
    """Получает список stash"""
    result = run_git_command(["stash", "list"], cwd=repo_path)
    
    if not result["success"]:
        return result
    
    stashes = []
    for line in result["stdout"].split("\n"):
        if line:
            stashes.append(line)
    
    return {
        "success": True,
        "stashes": stashes,
        "count": len(stashes)
    }


def git_stash_pop(repo_path: str, index: Optional[int] = None) -> Dict[str, Any]:
    """Извлекает stash с удалением"""
    args = ["stash", "pop"]
    if index is not None:
        args.append(f"stash@{{{index}}}")
    
    result = run_git_command(args, cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "message": "Stash popped",
        "output": result["stdout"]
    }


def git_stash_apply(repo_path: str, index: Optional[int] = None) -> Dict[str, Any]:
    """Применяет stash без удаления"""
    args = ["stash", "apply"]
    if index is not None:
        args.append(f"stash@{{{index}}}")
    
    result = run_git_command(args, cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "message": "Stash applied",
        "output": result["stdout"]
    }


def git_resolve_conflict(repo_path: str, path: str) -> Dict[str, Any]:
    """Отмечает файл как разрешённый после конфликта"""
    result = run_git_command(["add", path], cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "path": path,
        "message": f"Конфликт в файле {path} разрешён"
    }


def git_reset_soft(repo_path: str, target: str) -> Dict[str, Any]:
    """Мягкий сброс до указанного коммита (сохраняет изменения)"""
    result = run_git_command(["reset", "--soft", target], cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "target": target,
        "message": f"Выполнен мягкий сброс до {target}"
    }


def git_reset_hard(repo_path: str, target: str) -> Dict[str, Any]:
    """Жёсткий сброс до указанного коммита (теряет изменения)"""
    result = run_git_command(["reset", "--hard", target], cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "target": target,
        "message": f"Выполнен жёсткий сброс до {target}"
    }


def git_pull(repo_path: str, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
    """Pull изменения из удалённого репозитория"""
    args = ["pull", remote]
    if branch:
        args.append(branch)
    
    result = run_git_command(args, cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "output": result["stdout"],
        "message": "Изменения получены из удалённого репозитория"
    }


def git_push(repo_path: str, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """Push изменений в удалённый репозиторий"""
    args = ["push", remote]
    if force:
        args.append("--force")
    if branch:
        args.append(branch)
    
    result = run_git_command(args, cwd=repo_path)
    
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "output": result["stdout"],
        "message": "Изменения отправлены в удалённый репозиторий"
    }
