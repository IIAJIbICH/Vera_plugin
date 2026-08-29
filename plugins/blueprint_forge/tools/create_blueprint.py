"""
Blueprint Forge - Инструменты для создания Actor Blueprint с компонентами
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


class CreateBlueprintTool(Tool):
    """Создание Actor Blueprint с компонентами"""
    
    name = "create_blueprint"
    description = "Создаёт новый Actor Blueprint с указанными компонентами (Static Mesh, Collision, Light и др.)"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_name": {
                "type": "string",
                "description": "Имя создаваемого Blueprint"
            },
            "components": {
                "type": "array",
                "description": "Список компонентов для добавления",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["static_mesh", "box_collision", "sphere_collision", 
                                     "capsule_collision", "directional_light", "point_light", 
                                     "spot_light", "camera", "audio", "particle_system"],
                            "description": "Тип компонента"
                        },
                        "name": {
                            "type": "string",
                            "description": "Имя компонента"
                        },
                        "properties": {
                            "type": "object",
                            "description": "Свойства компонента (опционально)"
                        }
                    },
                    "required": ["type", "name"]
                }
            },
            "parent_class": {
                "type": "string",
                "description": "Родительский класс (по умолчанию Actor)",
                "default": "Actor"
            }
        },
        "required": ["blueprint_name", "components"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        blueprint_name = args.get("blueprint_name")
        components = args.get("components", [])
        parent_class = args.get("parent_class", "Actor")
        
        # Формируем Python скрипт для Unreal Editor
        script = f'''
import unreal
import json

def create_blueprint_with_components():
    try:
        # Создаём новый Blueprint
        blueprint_factory = unreal.BlueprintFactory()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        
        # Определяем путь для сохранения (в папке Content)
        package_path = "/Game/Blueprints"
        
        # Создаём папку если не существует
        if not unreal.EditorAssetLibrary.does_directory_exist(package_path):
            unreal.EditorAssetLibrary.make_directory(package_path)
        
        # Создаём Blueprint
        blueprint = blueprint_factory.create_blueprint(parent_class="{parent_class}")
        if blueprint is None:
            # Альтернативный способ создания
            blueprint = unreal.EditorAssetLibrary.create_asset(
                asset_class=unreal.Blueprint,
                package_path=package_path,
                asset_name="{blueprint_name}"
            )
        
        # Получаем скелетон граф
        skeleton_graph = blueprint.skeleton_generated_class
        event_graph = blueprint.event_graph
        
        # Добавляем компоненты
        blueprint_class = blueprint.generated_class
        if blueprint_class is None:
            blueprint_class = skeleton_graph
        
        components_added = []
        
        for comp_data in {json.dumps(components)}:
            comp_type = comp_data.get("type")
            comp_name = comp_data.get("name", comp_type)
            comp_props = comp_data.get("properties", {{}})
            
            component = None
            
            if comp_type == "static_mesh":
                component = unreal.StaticMeshComponent()
                component.set_editor_property("collision_enabled", unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            elif comp_type == "box_collision":
                component = unreal.BoxCollisionComponent()
                if "box_extent" in comp_props:
                    extent = comp_props["box_extent"]
                    component.set_editor_property("box_extent", unreal.Vector(*extent))
            elif comp_type == "sphere_collision":
                component = unreal.SphereCollisionComponent()
                if "sphere_radius" in comp_props:
                    component.set_editor_property("sphere_radius", comp_props["sphere_radius"])
            elif comp_type == "capsule_collision":
                component = unreal.CapsuleCollisionComponent()
                if "capsule_half_height" in comp_props:
                    component.set_editor_property("capsule_half_height", comp_props["capsule_half_height"])
                if "capsule_radius" in comp_props:
                    component.set_editor_property("capsule_radius", comp_props["capsule_radius"])
            elif comp_type == "directional_light":
                component = unreal.DirectionalLightComponent()
            elif comp_type == "point_light":
                component = unreal.PointLightComponent()
            elif comp_type == "spot_light":
                component = unreal.SpotLightComponent()
            elif comp_type == "camera":
                component = unreal.CameraComponent()
            elif comp_type == "audio":
                component = unreal.AudioComponent()
            elif comp_type == "particle_system":
                component = unreal.ParticleSystemComponent()
            
            if component is not None:
                component.set_editor_property("attach_parent", blueprint_class.get_root_component())
                component.set_editor_property("name", comp_name)
                
                # Применяем дополнительные свойства
                for prop_name, prop_value in comp_props.items():
                    if prop_name not in ["box_extent", "sphere_radius", "capsule_half_height", "capsule_radius"]:
                        try:
                            component.set_editor_property(prop_name, prop_value)
                        except:
                            pass
                
                blueprint_class.add_instance_component(component)
                components_added.append(comp_name)
        
        # Сохраняем Blueprint
        asset_tools.register_asset(blueprint, package_path)
        unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
        
        blueprint_path = f"{{package_path}}/{{blueprint_name}}"
        
        return {{
            "success": True,
            "blueprint_path": blueprint_path,
            "components_added": components_added,
            "message": f"Blueprint '{{blueprint_name}}' создан с {{len(components_added)}} компонентами"
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка создания Blueprint: {{str(e)}}"
        }}

result = create_blueprint_with_components()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Blueprint успешно создан")
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
