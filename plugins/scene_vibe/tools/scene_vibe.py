"""
Scene Vibe - Инструменты для применения настроения сцены
"""

import json
from typing import Any, Dict

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


# Пресеты настроений
MOOD_PRESETS = {
    "day": {
        "light_color": [1.0, 0.98, 0.95],
        "light_intensity": 10.0,
        "light_angle": 45.0,
        "sky_color": [0.4, 0.6, 0.9],
        "fog_density": 0.02,
        "exposure": 1.0,
        "contrast": 1.0,
        "saturation": 1.1,
        "temp": 6500
    },
    "night": {
        "light_color": [0.2, 0.25, 0.4],
        "light_intensity": 0.5,
        "light_angle": -30.0,
        "sky_color": [0.05, 0.05, 0.15],
        "fog_density": 0.05,
        "exposure": 0.5,
        "contrast": 1.2,
        "saturation": 0.8,
        "temp": 4000
    },
    "sunset": {
        "light_color": [1.0, 0.6, 0.3],
        "light_intensity": 5.0,
        "light_angle": 15.0,
        "sky_color": [0.9, 0.5, 0.3],
        "fog_density": 0.03,
        "exposure": 0.9,
        "contrast": 1.1,
        "saturation": 1.3,
        "temp": 3500
    },
    "horror": {
        "light_color": [0.3, 0.4, 0.3],
        "light_intensity": 1.0,
        "light_angle": 60.0,
        "sky_color": [0.1, 0.15, 0.1],
        "fog_density": 0.1,
        "exposure": 0.6,
        "contrast": 1.5,
        "saturation": 0.5,
        "temp": 5000
    },
    "sci-fi": {
        "light_color": [0.3, 0.6, 0.9],
        "light_intensity": 8.0,
        "light_angle": 50.0,
        "sky_color": [0.2, 0.3, 0.5],
        "fog_density": 0.04,
        "exposure": 1.1,
        "contrast": 1.3,
        "saturation": 1.2,
        "temp": 8000
    },
    "warm": {
        "light_color": [1.0, 0.85, 0.6],
        "light_intensity": 6.0,
        "light_angle": 40.0,
        "sky_color": [0.8, 0.6, 0.4],
        "fog_density": 0.02,
        "exposure": 1.0,
        "contrast": 0.9,
        "saturation": 1.2,
        "temp": 4500
    },
    "cold": {
        "light_color": [0.7, 0.8, 1.0],
        "light_intensity": 7.0,
        "light_angle": 55.0,
        "sky_color": [0.5, 0.6, 0.8],
        "fog_density": 0.03,
        "exposure": 1.0,
        "contrast": 1.1,
        "saturation": 0.9,
        "temp": 7500
    }
}


class SetVibeTool(Tool):
    """Применение настроения сцены"""
    
    name = "set_vibe"
    description = "Применяет настроение сцены через настройку DirectionalLight и PostProcessVolume"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "mood": {
                "type": "string",
                "enum": ["day", "night", "sunset", "horror", "sci-fi", "warm", "cold"],
                "description": "Тип настроения"
            },
            "intensity": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Интенсивность эффекта (0.0-1.0)",
                "default": 1.0
            },
            "create_volume": {
                "type": "boolean",
                "description": "Создать новый PostProcessVolume если не существует",
                "default": True
            }
        },
        "required": ["mood"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        mood = args.get("mood")
        intensity = args.get("intensity", 1.0)
        create_volume = args.get("create_volume", True)
        
        preset = MOOD_PRESETS.get(mood)
        if not preset:
            return ToolResult(
                success=False,
                error=f"Неизвестное настроение: {mood}",
                message=f"Доступные настроения: {list(MOOD_PRESETS.keys())}"
            )
        
        # Применяем интенсивность
        for key in ["light_intensity", "fog_density", "exposure"]:
            preset[key] = preset[key] * intensity if key != "fog_density" else preset[key] * (0.5 + intensity * 0.5)
        
        script = f'''
import unreal
import json

def set_scene_vibe():
    try:
        preset = {json.dumps(preset)}
        mood = "{mood}"
        create_volume = {str(create_volume)}
        
        actors_modified = 0
        
        # Находим или создаём DirectionalLight
        directional_lights = unreal.EditorLevelLibrary.get_all_level_actors_of_class(unreal.DirectionalLight)
        directional_light = None
        
        if directional_lights:
            directional_light = directional_lights[0]
        else:
            # Создаём новый DirectionalLight
            actor_class = unreal.DirectionalLight.static_class()
            spawn_location = unreal.Vector(0, 0, 500)
            spawn_rotation = unreal.Rotator(-{preset["light_angle"]}, 0, 0)
            directional_light = unreal.EditorLevelLibrary.spawn_actor_from_class(
                actor_class, spawn_location, spawn_rotation
            )
            directional_light.set_actor_label(f"Vibe_DirectionalLight_{{mood}}")
            actors_modified += 1
        
        # Настраиваем DirectionalLight
        light_component = directional_light.get_component_by_class(unreal.DirectionalLightComponent)
        if light_component:
            light_color = unreal.LinearColor(*preset["light_color"], 1.0)
            light_component.set_editor_property("light_color", light_color)
            light_component.set_editor_property("intensity", preset["light_intensity"])
            light_component.set_editor_property("temperature", preset["temp"])
        
        # Находим или создаём PostProcessVolume
        ppv_class = unreal.PostProcessVolume.static_class()
        ppv_actors = unreal.EditorLevelLibrary.get_all_level_actors_of_class(ppv_class)
        ppv = None
        
        for actor in ppv_actors:
            label = actor.get_actor_label()
            if "Vibe_" in label or "PostProcess" in label:
                ppv = actor
                break
        
        if ppv is None and create_volume:
            spawn_location = unreal.Vector(0, 0, 0)
            spawn_rotation = unreal.Rotator(0, 0, 0)
            ppv = unreal.EditorLevelLibrary.spawn_actor_from_class(
                ppv_class, spawn_location, spawn_rotation
            )
            ppv.set_actor_label(f"Vibe_PostProcess_{{mood}}")
            
            # Устанавливаем бесконечный extents
            ppv_component = ppv.get_component_by_class(unreal.PostProcessComponent)
            if ppv_component:
                ppv_component.set_editor_property("b_unbound", True)
                ppv_component.set_editor_property("infinity_settings", 
                    unreal.PostProcessSettingsInfiniteType.PPIS_INFINITE)
            actors_modified += 1
        elif ppv is None:
            ppv = ppv_actors[0] if ppv_actors else None
        
        if ppv:
            ppv_component = ppv.get_component_by_class(unreal.PostProcessComponent)
            if ppv_component:
                settings = ppv_component.get_editor_property("settings")
                
                # Настраиваем пост-обработку
                settings.color_grading_mode = unreal.ColorGradingMode.CGM_COLOR_GRADING_MODE_CAT
                settings.auto_exposure_bias = preset["exposure"] - 1.0
                
                # Контраст и насыщенность
                shadows = unreal.Vector4(0, 0, 0, preset["contrast"])
                midtones = unreal.Vector4(0, 0, 0, preset["saturation"])
                highlights = unreal.Vector4(0, 0, 0, preset["contrast"])
                
                settings.color_grading_shadows = unreal.ColorGradingChannels(shadows, shadows, shadows)
                settings.color_grading_midtones = unreal.ColorGradingChannels(midtones, midtones, midtones)
                settings.color_grading_highlights = unreal.ColorGradingChannels(highlights, highlights, highlights)
                
                # Fog/Atmosphere
                settings.fog_density = preset["fog_density"]
                
                ppv_component.set_editor_property("settings", settings)
                actors_modified += 1
        
        # Сохраняем изменения
        unreal.EditorLevelLibrary.save_current_level()
        
        return {{
            "success": True,
            "mood": mood,
            "actors_modified": actors_modified,
            "message": f"Настроение '{{mood}}' применено, изменено {{actors_modified}} акторов"
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка применения настроения: {{str(e)}}"
        }}

result = set_scene_vibe()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Настроение успешно применено")
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


class ClearVibeTool(Tool):
    """Удаление всех помеченных акторов Scene Vibe"""
    
    name = "clear_vibe"
    description = "Удаляет все помеченные акторы, созданные плагином Scene Vibe (DirectionalLight, PostProcessVolume)"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "confirm": {
                "type": "boolean",
                "description": "Подтверждение удаления (обязательно true)"
            }
        },
        "required": ["confirm"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        confirm = args.get("confirm", False)
        
        if not confirm:
            return ToolResult(
                success=False,
                error="Требуется подтверждение удаления",
                message="Передайте confirm=true для удаления акторов"
            )
        
        script = '''
import unreal
import json

def clear_vibe_actors():
    try:
        actors_deleted = 0
        
        # Получаем все акторы уровня
        all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
        
        for actor in all_actors:
            label = actor.get_actor_label()
            
            # Удаляем акторы с меткой Vibe_
            if label.startswith("Vibe_"):
                actor_class = actor.get_class()
                actor_name = actor_class.get_name()
                
                # Не удаляем критические акторы
                if actor_name in ["PlayerStart", "WorldSettings"]:
                    continue
                
                unreal.EditorLevelLibrary.destroy_actor(actor)
                actors_deleted += 1
        
        # Сохраняем изменения
        unreal.EditorLevelLibrary.save_current_level()
        
        return {
            "success": True,
            "actors_deleted": actors_deleted,
            "message": f"Удалено {actors_deleted} акторов Scene Vibe"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка очистки: {str(e)}"
        }

result = clear_vibe_actors()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Акторы успешно удалены")
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
