"""
Mobile Performance Doctor - Анализ производительности и совместимости
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import Tool, ToolResult, ToolContext
from ..exceptions import UEConnectionError, UETimeoutError


def send_json(bridge_port: int, data: dict) -> dict:
    """Отправка JSON-скрипта в редактор Unreal через bridge"""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(30)
        message = json.dumps(data).encode('utf-8')
        sock.sendto(message, ('127.0.0.1', bridge_port))
        response, _ = sock.recvfrom(65536)
        sock.close()
        return json.loads(response.decode('utf-8'))
    except socket.timeout:
        raise UETimeoutError("Превышено время ожидания ответа от Unreal Editor")
    except Exception as e:
        raise UEConnectionError(f"Ошибка соединения с Unreal Editor: {e}")


# Проблемы мобильных материалов
MOBILE_ISSUES = {
    "high_complexity": {
        "severity": "high",
        "description": "Слишком сложный шейдер для мобильных устройств"
    },
    "translucency": {
        "severity": "medium", 
        "description": "Полупрозрачность может быть проблематичной на мобильных"
    },
    "dynamic_lighting": {
        "severity": "high",
        "description": "Динамическое освещение дорого для мобильных"
    },
    "large_textures": {
        "severity": "medium",
        "description": "Текстуры высокого разрешения потребляют много памяти"
    },
    "normal_maps": {
        "severity": "low",
        "description": "Нормал мапы увеличивают сложность шейдера"
    },
    "parallax": {
        "severity": "high",
        "description": "Параллакс окклюзия очень дорога для мобильных"
    }
}


def scan_materials_filesystem(content_path: str, strict_mode: bool = False) -> Dict[str, Any]:
    """Сканирует материалы через файловую систему (без редактора)"""
    issues = []
    materials_scanned = 0
    
    content_dir = Path(content_path)
    if not content_dir.exists():
        return {"success": False, "error": "Content directory not found"}
    
    # Ищем все .uasset файлы материалов
    for material_file in content_dir.rglob("*.uasset"):
        materials_scanned += 1
        
        # Простая эвристика по имени и размеру
        file_size = material_file.stat().st_size
        file_name = material_file.name.lower()
        
        material_issues = []
        
        # Проверяем по имени на потенциальные проблемы
        if any(x in file_name for x in ["glass", "water", "transparent"]):
            material_issues.append({
                "issue": "translucency",
                **MOBILE_ISSUES["translucency"]
            })
        
        if any(x in file_name for x in ["detail", "complex", "master"]):
            material_issues.append({
                "issue": "high_complexity",
                **MOBILE_ISSUES["high_complexity"]
            })
        
        # Большие файлы могут иметь большие текстуры
        if file_size > 1024 * 1024:  # > 1MB
            material_issues.append({
                "issue": "large_textures",
                **MOBILE_ISSUES["large_textures"]
            })
        
        if strict_mode:
            # В строгом режиме добавляем больше проверок
            if any(x in file_name for x in ["normal", "nrm"]):
                material_issues.append({
                    "issue": "normal_maps",
                    **MOBILE_ISSUES["normal_maps"]
                })
        
        if material_issues:
            issues.append({
                "path": str(material_file.relative_to(content_dir)),
                "issues": material_issues
            })
    
    # Рассчитываем риск
    risk_score = min(100, len(issues) * 5)
    
    return {
        "success": True,
        "materials_scanned": materials_scanned,
        "issues": issues,
        "risk_score": risk_score
    }


class CheckMobileCompatTool(Tool):
    """Проверка совместимости с мобильными устройствами"""
    
    name = "check_mobile_compat"
    description = "Сканирует материалы проекта на риски для мобильных устройств"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Путь к проекту (по умолчанию используется текущий проект)"
            },
            "strict_mode": {
                "type": "boolean",
                "description": "Строгий режим проверки",
                "default": False
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        project_path = args.get("project_path", ctx.project_path)
        strict_mode = args.get("strict_mode", False)
        
        content_path = os.path.join(project_path, "Content")
        
        if not os.path.exists(content_path):
            return ToolResult(
                success=False,
                error="Директория Content не найдена",
                message=f"Путь {content_path} не существует"
            )
        
        result = scan_materials_filesystem(content_path, strict_mode)
        
        if not result.get("success"):
            return ToolResult(
                success=False,
                error=result.get("error", "Неизвестная ошибка"),
                message="Ошибка сканирования материалов"
            )
        
        issues_count = len(result.get("issues", []))
        
        return ToolResult(
            success=True,
            data=result,
            message=f"Проверено {result.get('materials_scanned')} материалов, найдено проблем: {issues_count}, риск: {result.get('risk_score')}%"
        )


class FindExpensiveMaterialsTool(Tool):
    """Поиск тяжёлых материалов"""
    
    name = "find_expensive_materials"
    description = "Находит и ранжирует материалы по тяжести шейдеров"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Путь к проекту (по умолчанию используется текущий проект)"
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "description": "Максимальное количество результатов",
                "default": 20
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        project_path = args.get("project_path", ctx.project_path)
        limit = args.get("limit", 20)
        
        content_path = os.path.join(project_path, "Content")
        
        if not os.path.exists(content_path):
            return ToolResult(
                success=False,
                error="Директория Content не найдена",
                message=f"Путь {content_path} не существует"
            )
        
        # Сканируем материалы
        result = scan_materials_filesystem(content_path, strict_mode=True)
        
        if not result.get("success"):
            return ToolResult(
                success=False,
                error=result.get("error", "Неизвестная ошибка"),
                message="Ошибка сканирования материалов"
            )
        
        # Сортируем по количеству проблем
        materials = []
        for item in result.get("issues", []):
            complexity_score = len(item.get("issues", [])) * 25
            materials.append({
                "path": item["path"],
                "complexity_score": min(100, complexity_score),
                "issues": [i["issue"] for i in item.get("issues", [])]
            })
        
        materials.sort(key=lambda x: x["complexity_score"], reverse=True)
        materials = materials[:limit]
        
        return ToolResult(
            success=True,
            data={
                "materials": materials,
                "count": len(materials)
            },
            message=f"Найдено {len(materials)} тяжёлых материалов"
        )


class ProfileLevelTool(Tool):
    """Профилирование уровня"""
    
    name = "profile_level"
    description = "Профилирует открытый уровень: акторы, треугольники, огни"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "include_hidden": {
                "type": "boolean",
                "description": "Включать скрытые акторы",
                "default": False
            }
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        include_hidden = args.get("include_hidden", False)
        
        script = f'''
import unreal
import json

def profile_current_level():
    try:
        include_hidden = {str(include_hidden)}
        
        # Получаем все акторы уровня
        all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
        
        actor_count = 0
        triangle_count = 0
        dynamic_light_count = 0
        static_light_count = 0
        memory_estimate = 0
        
        for actor in all_actors:
            # Пропускаем скрытые если нужно
            if not include_hidden and not actor.is_visible():
                continue
            
            actor_count += 1
            actor_class = actor.get_class().get_name()
            
            # Считаем огни
            if "Light" in actor_class:
                if "Directional" in actor_class or "Point" in actor_class or "Spot" in actor_class:
                    # Проверяем мобильность
                    light_comp = actor.get_component_by_class(unreal.LightComponent)
                    if light_comp:
                        mobility = light_comp.get_editor_property("mobility")
                        if mobility == unreal.ComponentMobility.Movable:
                            dynamic_light_count += 1
                        else:
                            static_light_count += 1
            
            # Считаем треугольники от статических мешей
            static_mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if static_mesh_comp:
                static_mesh = static_mesh_comp.get_editor_property("static_mesh")
                if static_mesh:
                    # Получаем количество треугольников
                    lod_data = static_mesh.get_render_data()
                    if lod_data:
                        triangle_count += lod_data.total_triangles
                    
                    # Оценка памяти
                    memory_estimate += static_mesh.get_resource_size()
        
        # Определяем рейтинг производительности
        if triangle_count < 100000 and dynamic_light_count < 5:
            rating = "good"
        elif triangle_count < 500000 and dynamic_light_count < 20:
            rating = "fair"
        else:
            rating = "poor"
        
        return {{
            "success": True,
            "actor_count": actor_count,
            "triangle_count": triangle_count,
            "dynamic_light_count": dynamic_light_count,
            "static_light_count": static_light_count,
            "memory_estimate_mb": round(memory_estimate / (1024 * 1024), 2),
            "performance_rating": rating
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e)
        }}

result = profile_current_level()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                rating = response.get("performance_rating", "unknown")
                return ToolResult(
                    success=True,
                    data=response,
                    message=f"Уровень: {response.get('actor_count')} акторов, {response.get('triangle_count')} триугольников, рейтинг: {rating}"
                )
            else:
                return ToolResult(
                    success=False,
                    data=response,
                    message=response.get("error", "Неизвестная ошибка")
                )
                
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"Ошибка связи с Unreal Editor: {e}"
            )
