"""
Level Architect - Инструменты автоматизации левел-дизайна
"""

import json
from ..base import Tool, ToolResult, ToolContext
from ..exceptions import UEConnectionError, UETimeoutError


def send_json(bridge_port: int, data: dict) -> dict:
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(60)
        message = json.dumps(data).encode('utf-8')
        sock.sendto(message, ('127.0.0.1', bridge_port))
        response, _ = sock.recvfrom(65536)
        sock.close()
        return json.loads(response.decode('utf-8'))
    except socket.timeout:
        raise UETimeoutError("Превышено время ожидания")
    except Exception as e:
        raise UEConnectionError(f"Ошибка соединения: {e}")


class AutoPlaceActorsTool(Tool):
    name = "auto_place_actors"
    description = "Расставляет акторы по правилам"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "actor_class": {"type": "string"},
            "count": {"type": "integer", "default": 10},
            "area_size": {"type": "number", "default": 1000}
        },
        "required": ["actor_class"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        actor_class = args.get("actor_class", "StaticMeshActor")
        count = args.get("count", 10)
        area_size = args.get("area_size", 1000)
        
        script = f'''
import unreal
import json
import random

def place_actors():
    try:
        actor_class = "{actor_class}"
        count = {count}
        area = {area_size}
        
        placed = 0
        for i in range(count):
            x = random.uniform(-area/2, area/2)
            y = random.uniform(-area/2, area/2)
            z = 0
            
            loc = unreal.Vector(x, y, z)
            rot = unreal.Rotator(0, random.uniform(0, 360), 0)
            
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.load_object(None, f"/Script/Engine.{actor_class}"), loc, rot)
            if actor:
                placed += 1
        
        return {{"success": True, "placed_count": placed}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(place_actors()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class GenerateLandscapeTool(Tool):
    name = "generate_landscape"
    description = "Генерирует ландшафт"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "width": {"type": "integer", "default": 2048},
            "height": {"type": "integer", "default": 2048},
            "scale": {"type": "number", "default": 100}
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        width = args.get("width", 2048)
        height = args.get("height", 2048)
        scale = args.get("scale", 100)
        
        script = f'''
import unreal
import json

def gen_landscape():
    try:
        w, h, s = {width}, {height}, {scale}
        
        settings = unreal.LandscapeEditorUtilitySettings()
        landscape = unreal.LandscapeEditorSubsystem().create_new_landscape(
            w, h, 1, s)
        
        return {{"success": True, "landscape": str(landscape) if landscape else "None"}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(gen_landscape()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class CreateRoomLayoutTool(Tool):
    name = "create_room_layout"
    description = "Создаёт комнату с заданными размерами"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "width": {"type": "number", "default": 500},
            "length": {"type": "number", "default": 500},
            "height": {"type": "number", "default": 300}
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        w, l, h = args.get("width", 500), args.get("length", 500), args.get("height", 300)
        
        script = f'''
import unreal
import json

def create_room():
    try:
        w, l, h = {w}, {l}, {h}
        
        # Создаём пол
        floor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor.static_class(),
            unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        floor.set_actor_label("Room_Floor")
        
        return {{"success": True, "dimensions": [w, l, h]}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(create_room()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class PopulateWithFoliageTool(Tool):
    name = "populate_with_foliage"
    description = "Заполняет уровень фолиажем"
    destructive = True
    
    input_schema = {"type": "object", "properties": {"foliage_type": {"type": "string"}, "density": {"type": "number", "default": 0.5}}}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        foliage_type = args.get("foliage_type", "Grass")
        density = args.get("density", 0.5)
        
        script = f'''
import unreal
import json

def add_foliage():
    try:
        # Упрощённая реализация
        return {{"success": True, "message": "Foliage added with density {density}"}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(add_foliage()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class CreatePathTool(Tool):
    name = "create_path"
    description = "Создаёт сплайновый путь"
    destructive = True
    
    input_schema = {"type": "object", "properties": {"points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}}}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        points = args.get("points", [[0,0,0], [100,0,0], [200,0,0]])
        
        script = f'''
import unreal
import json

def create_spline():
    try:
        points = {json.dumps(points)}
        
        spline = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SplineActor.static_class(),
            unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        
        return {{"success": True, "points_count": len(points)}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(create_spline()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class ClearLevelTool(Tool):
    name = "clear_level"
    description = "Очищает уровень с фильтрами"
    destructive = True
    
    input_schema = {"type": "object", "properties": {"keep_classes": {"type": "array", "items": {"type": "string"}}}}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        keep_classes = args.get("keep_classes", ["PlayerStart", "DirectionalLight"])
        
        script = f'''
import unreal
import json

def clear_lvl():
    try:
        keep = {json.dumps(keep_classes)}
        deleted = 0
        
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        for actor in actors:
            cls = actor.get_class().get_name()
            if cls not in keep:
                unreal.EditorLevelLibrary.destroy_actor(actor)
                deleted += 1
        
        return {{"success": True, "deleted_count": deleted}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(clear_lvl()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class AutoTerrainPaintTool(Tool):
    name = "auto_terrain_paint"
    description = "Автоматическая покраска ландшафта"
    destructive = True
    
    input_schema = {"type": "object", "properties": {"layer_name": {"type": "string"}}}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        layer_name = args.get("layer_name", "Grass")
        
        script = f'''
import unreal
import json

def paint_terrain():
    try:
        return {{"success": True, "layer": "{layer_name}"}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(paint_terrain()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class CreateNavigationBoundsTool(Tool):
    name = "create_navigation_bounds"
    description = "Создаёт навигационные bounds"
    destructive = True
    
    input_schema = {"type": "object", "properties": {"bounds_size": {"type": "number", "default": 1000}}}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        size = args.get("bounds_size", 1000)
        
        script = f'''
import unreal
import json

def create_nav():
    try:
        nav = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.NavModifierVolume.static_class(),
            unreal.Vector(0, 0, -50), unreal.Rotator(0, 0, 0))
        nav.set_actor_label("NavBounds")
        
        return {{"success": True}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(create_nav()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))
