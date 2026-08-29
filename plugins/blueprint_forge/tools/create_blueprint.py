"""
Blueprint Forge - Полный набор инструментов для работы с Blueprint
"""

import json
from typing import Any, Dict

from plugins.base import Tool, ToolResult, ToolContext
from plugins.exceptions import UEConnectionError, UETimeoutError


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
        
        script = f'''
import unreal
import json

def create_blueprint_with_components():
    try:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        package_path = "/Game/Blueprints"
        
        if not unreal.EditorAssetLibrary.does_directory_exist(package_path):
            unreal.EditorAssetLibrary.make_directory(package_path)
        
        blueprint_factory = unreal.BlueprintFactory()
        blueprint = blueprint_factory.create_blueprint(parent_class="{parent_class}")
        
        if blueprint is None:
            blueprint = unreal.EditorAssetLibrary.create_asset(
                asset_class=unreal.Blueprint,
                package_path=package_path,
                asset_name="{blueprint_name}"
            )
        
        skeleton_graph = blueprint.skeleton_generated_class
        event_graph = blueprint.event_graph
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
            elif comp_type == "sphere_collision":
                component = unreal.SphereCollisionComponent()
            elif comp_type == "capsule_collision":
                component = unreal.CapsuleCollisionComponent()
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
                
                for prop_name, prop_value in comp_props.items():
                    try:
                        component.set_editor_property(prop_name, prop_value)
                    except:
                        pass
                
                blueprint_class.add_instance_component(component)
                components_added.append(comp_name)
        
        asset_tools.register_asset(blueprint, package_path)
        unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
        
        blueprint_path = f"{{package_path}}/{blueprint_name}"
        
        return {{
            "success": True,
            "blueprint_path": blueprint_path,
            "components_added": components_added,
            "message": f"Blueprint создан с {{len(components_added)}} компонентами"
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


class DuplicateBlueprintTool(Tool):
    """Клонирование существующего Blueprint"""
    
    name = "duplicate_blueprint"
    description = "Создаёт копию существующего Blueprint с новым именем"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "source_blueprint": {
                "type": "string",
                "description": "Путь к исходному Blueprint (например, /Game/Blueprints/OldBP)"
            },
            "new_name": {
                "type": "string",
                "description": "Имя для нового Blueprint"
            },
            "destination_path": {
                "type": "string",
                "description": "Путь назначения (по умолчанию /Game/Blueprints)",
                "default": "/Game/Blueprints"
            }
        },
        "required": ["source_blueprint", "new_name"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        source_bp = args.get("source_blueprint")
        new_name = args.get("new_name")
        dest_path = args.get("destination_path", "/Game/Blueprints")
        
        script = f'''
import unreal
import json

def duplicate_blueprint():
    try:
        source_path = "{source_bp}"
        new_name = "{new_name}"
        dest_path = "{dest_path}"
        
        if not unreal.EditorAssetLibrary.does_directory_exist(dest_path):
            unreal.EditorAssetLibrary.make_directory(dest_path)
        
        source_asset = unreal.EditorAssetLibrary.load_asset(source_path)
        if source_asset is None:
            return {{
                "success": False,
                "error": f"Не удалось загрузить Blueprint: {{source_path}}",
                "message": "Проверьте путь к исходному Blueprint"
            }}
        
        new_full_path = f"{{dest_path}}/{{new_name}}"
        
        result = unreal.EditorAssetLibrary.duplicate_asset(source_path, new_full_path)
        
        if result:
            unreal.EditorAssetLibrary.save_loaded_asset(unreal.EditorAssetLibrary.load_asset(new_full_path))
            return {{
                "success": True,
                "new_path": new_full_path,
                "message": f"Blueprint скопирован в {{new_full_path}}"
            }}
        else:
            return {{
                "success": False,
                "error": "Не удалось создать копию",
                "message": "Ошибка дублирования актива"
            }}
            
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка: {{str(e)}}"
        }}

result = duplicate_blueprint()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Blueprint успешно клонирован")
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


class AddComponentToBlueprintTool(Tool):
    """Добавление компонента в существующий Blueprint"""
    
    name = "add_component_to_blueprint"
    description = "Добавляет новый компонент в существующий Blueprint"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {
                "type": "string",
                "description": "Путь к Blueprint (например, /Game/Blueprints/MyBP)"
            },
            "component_type": {
                "type": "string",
                "enum": ["static_mesh", "box_collision", "sphere_collision", 
                         "capsule_collision", "directional_light", "point_light", 
                         "spot_light", "camera", "audio", "particle_system"],
                "description": "Тип добавляемого компонента"
            },
            "component_name": {
                "type": "string",
                "description": "Имя компонента"
            },
            "properties": {
                "type": "object",
                "description": "Свойства компонента (опционально)"
            }
        },
        "required": ["blueprint_path", "component_type", "component_name"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        comp_type = args.get("component_type")
        comp_name = args.get("component_name")
        comp_props = args.get("properties", {})
        
        script = f'''
import unreal
import json

def add_component():
    try:
        bp_path = "{bp_path}"
        comp_type = "{comp_type}"
        comp_name = "{comp_name}"
        comp_props = {json.dumps(comp_props)}
        
        blueprint = unreal.EditorAssetLibrary.load_asset(bp_path)
        if blueprint is None:
            return {{
                "success": False,
                "error": f"Blueprint не найден: {{bp_path}}",
                "message": "Проверьте путь к Blueprint"
            }}
        
        blueprint_class = blueprint.generated_class
        if blueprint_class is None:
            blueprint_class = blueprint.skeleton_generated_class
        
        component = None
        
        if comp_type == "static_mesh":
            component = unreal.StaticMeshComponent()
        elif comp_type == "box_collision":
            component = unreal.BoxCollisionComponent()
        elif comp_type == "sphere_collision":
            component = unreal.SphereCollisionComponent()
        elif comp_type == "capsule_collision":
            component = unreal.CapsuleCollisionComponent()
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
        
        if component is None:
            return {{
                "success": False,
                "error": f"Неизвестный тип компонента: {{comp_type}}",
                "message": "Проверьте тип компонента"
            }}
        
        component.set_editor_property("name", comp_name)
        
        for prop_name, prop_value in comp_props.items():
            try:
                component.set_editor_property(prop_name, prop_value)
            except:
                pass
        
        root_comp = blueprint_class.get_root_component()
        if root_comp:
            component.set_editor_property("attach_parent", root_comp)
        
        blueprint_class.add_instance_component(component)
        
        unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
        
        return {{
            "success": True,
            "component_name": comp_name,
            "component_type": comp_type,
            "message": f"Компонент '{{comp_name}}' добавлен в Blueprint"
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка добавления компонента: {{str(e)}}"
        }}

result = add_component()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Компонент успешно добавлен")
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


class RemoveComponentFromBlueprintTool(Tool):
    """Удаление компонента из Blueprint"""
    
    name = "remove_component_from_blueprint"
    description = "Удаляет указанный компонент из Blueprint"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {
                "type": "string",
                "description": "Путь к Blueprint"
            },
            "component_name": {
                "type": "string",
                "description": "Имя удаляемого компонента"
            }
        },
        "required": ["blueprint_path", "component_name"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        comp_name = args.get("component_name")
        
        script = f'''
import unreal
import json

def remove_component():
    try:
        bp_path = "{bp_path}"
        comp_name = "{comp_name}"
        
        blueprint = unreal.EditorAssetLibrary.load_asset(bp_path)
        if blueprint is None:
            return {{
                "success": False,
                "error": f"Blueprint не найден: {{bp_path}}",
                "message": "Проверьте путь к Blueprint"
            }}
        
        blueprint_class = blueprint.generated_class
        if blueprint_class is None:
            blueprint_class = blueprint.skeleton_generated_class
        
        components = blueprint_class.get_components_by_name()
        component_to_remove = None
        
        for comp in components:
            if comp.get_editor_property("name") == comp_name:
                component_to_remove = comp
                break
        
        if component_to_remove is None:
            return {{
                "success": False,
                "error": f"Компонент '{{comp_name}}' не найден",
                "message": "Проверьте имя компонента"
            }}
        
        blueprint_class.remove_instance_component(component_to_remove)
        unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
        
        return {{
            "success": True,
            "component_name": comp_name,
            "message": f"Компонент '{{comp_name}}' удалён из Blueprint"
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка удаления компонента: {{str(e)}}"
        }}

result = remove_component()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Компонент успешно удалён")
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


class ListBlueprintComponentsTool(Tool):
    """Список компонентов Blueprint"""
    
    name = "list_blueprint_components"
    description = "Возвращает список всех компонентов указанного Blueprint"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {
                "type": "string",
                "description": "Путь к Blueprint"
            }
        },
        "required": ["blueprint_path"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        
        script = f'''
import unreal
import json

def list_components():
    try:
        bp_path = "{bp_path}"
        
        blueprint = unreal.EditorAssetLibrary.load_asset(bp_path)
        if blueprint is None:
            return {{
                "success": False,
                "error": f"Blueprint не найден: {{bp_path}}",
                "message": "Проверьте путь к Blueprint"
            }}
        
        blueprint_class = blueprint.generated_class
        if blueprint_class is None:
            blueprint_class = blueprint.skeleton_generated_class
        
        components = blueprint_class.get_components_by_name()
        components_list = []
        
        for comp in components:
            comp_info = {{
                "name": comp.get_editor_property("name"),
                "class": comp.get_class().get_name(),
                "is_inherited": comp.get_editor_property("is_inherited_component")
            }}
            components_list.append(comp_info)
        
        return {{
            "success": True,
            "blueprint_path": bp_path,
            "components": components_list,
            "total_count": len(components_list),
            "message": f"Найдено {{len(components_list)}} компонентов"
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка получения списка компонентов: {{str(e)}}"
        }}

result = list_components()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Список компонентов получен")
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


class CompileBlueprintTool(Tool):
    """Компиляция Blueprint"""
    
    name = "compile_blueprint"
    description = "Компилирует указанный Blueprint и проверяет наличие ошибок"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {
                "type": "string",
                "description": "Путь к Blueprint"
            }
        },
        "required": ["blueprint_path"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        
        script = f'''
import unreal
import json

def compile_blueprint():
    try:
        bp_path = "{bp_path}"
        
        blueprint = unreal.EditorAssetLibrary.load_asset(bp_path)
        if blueprint is None:
            return {{
                "success": False,
                "error": f"Blueprint не найден: {{bp_path}}",
                "message": "Проверьте путь к Blueprint"
            }}
        
        factory = unreal.BlueprintFactory()
        result = factory.compile_blueprint(blueprint)
        
        if result:
            unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
            return {{
                "success": True,
                "blueprint_path": bp_path,
                "message": "Blueprint успешно скомпилирован"
            }}
        else:
            return {{
                "success": False,
                "error": "Ошибка компиляции",
                "message": "Проверьте логи редактора для деталей"
            }}
            
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка компиляции: {{str(e)}}"
        }}

result = compile_blueprint()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Blueprint скомпилирован")
                )
            else:
                return ToolResult(
                    success=False,
                    data=response,
                    message=response.get("error", "Ошибка компиляции")
                )
                
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"Ошибка связи с Unreal Editor: {e}"
            )


class GetBlueprintVariablesTool(Tool):
    """Получение переменных Blueprint"""
    
    name = "get_blueprint_variables"
    description = "Возвращает список всех переменных (member variables) Blueprint"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {
                "type": "string",
                "description": "Путь к Blueprint"
            }
        },
        "required": ["blueprint_path"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        
        script = f'''
import unreal
import json

def get_variables():
    try:
        bp_path = "{bp_path}"
        
        blueprint = unreal.EditorAssetLibrary.load_asset(bp_path)
        if blueprint is None:
            return {{
                "success": False,
                "error": f"Blueprint не найден: {{bp_path}}",
                "message": "Проверьте путь к Blueprint"
            }}
        
        skeleton = blueprint.skeleton_generated_class
        variables = skeleton.get_member_variable_names()
        
        var_list = []
        for var_name in variables:
            var_info = skeleton.get_member_variable(var_name)
            var_list.append({{
                "name": var_name,
                "type": str(var_info.var_type) if var_info else "unknown",
                "is_public": var_info.is_public if var_info else False
            }})
        
        return {{
            "success": True,
            "blueprint_path": bp_path,
            "variables": var_list,
            "total_count": len(var_list),
            "message": f"Найдено {{len(var_list)}} переменных"
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка получения переменных: {{str(e)}}"
        }}

result = get_variables()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Переменные получены")
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


class SetBlueprintVariableTool(Tool):
    """Установка значения переменной Blueprint"""
    
    name = "set_blueprint_variable"
    description = "Устанавливает значение указанной переменной Blueprint"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {
                "type": "string",
                "description": "Путь к Blueprint"
            },
            "variable_name": {
                "type": "string",
                "description": "Имя переменной"
            },
            "value": {
                "type": ["string", "number", "boolean", "object"],
                "description": "Значение переменной"
            }
        },
        "required": ["blueprint_path", "variable_name", "value"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        var_name = args.get("variable_name")
        value = args.get("value")
        
        script = f'''
import unreal
import json

def set_variable():
    try:
        bp_path = "{bp_path}"
        var_name = "{var_name}"
        value = {json.dumps(value)}
        
        blueprint = unreal.EditorAssetLibrary.load_asset(bp_path)
        if blueprint is None:
            return {{
                "success": False,
                "error": f"Blueprint не найден: {{bp_path}}",
                "message": "Проверьте путь к Blueprint"
            }}
        
        skeleton = blueprint.skeleton_generated_class
        
        try:
            skeleton.set_member_variable_value(var_name, value)
            unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
            return {{
                "success": True,
                "blueprint_path": bp_path,
                "variable_name": var_name,
                "value": value,
                "message": f"Переменная '{{var_name}}' установлена в {{value}}"
            }}
        except Exception as ve:
            return {{
                "success": False,
                "error": f"Ошибка установки переменной: {{str(ve)}}",
                "message": "Возможно, неверный тип значения"
            }}
            
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка: {{str(e)}}"
        }}

result = set_variable()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Переменная установлена")
                )
            else:
                return ToolResult(
                    success=False,
                    data=response,
                    message=response.get("error", "Ошибка установки переменной")
                )
                
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"Ошибка связи с Unreal Editor: {e}"
            )lResult(
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


class RemoveComponentFromBlueprintTool(Tool):
    """Удаление компонента из Blueprint"""
    
    name = "remove_component_from_blueprint"
    description = "Удаляет указанный компонент из Blueprint"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {
                "type": "string",
                "description": "Путь к Blueprint"
            },
            "component_name": {
                "type": "string",
                "description": "Имя удаляемого компонента"
            }
        },
        "required": ["blueprint_path", "component_name"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        comp_name = args.get("component_name")
        
        script = f'''
import unreal
import json

def remove_component():
    try:
        bp_path = "{bp_path}"
        comp_name = "{comp_name}"
        
        blueprint = unreal.EditorAssetLibrary.load_asset(bp_path)
        if blueprint is None:
            return {{
                "success": False,
                "error": f"Blueprint не найден: {{bp_path}}",
                "message": "Проверьте путь к Blueprint"
            }}
        
        blueprint_class = blueprint.generated_class
        if blueprint_class is None:
            blueprint_class = blueprint.skeleton_generated_class
        
        components = blueprint_class.get_components_by_name()
        component_to_remove = None
        
        for comp in components:
            if comp.get_editor_property("name") == comp_name:
                component_to_remove = comp
                break
        
        if component_to_remove is None:
            return {{
                "success": False,
                "error": f"Компонент '{{comp_name}}' не найден",
                "message": "Проверьте имя компонента"
            }}
        
        blueprint_class.remove_instance_component(component_to_remove)
        unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
        
        return {{
            "success": True,
            "component_name": comp_name,
            "message": f"Компонент '{{comp_name}}' удалён из Blueprint"
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка удаления компонента: {{str(e)}}"
        }}

result = remove_component()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Компонент успешно удалён")
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


class ListBlueprintComponentsTool(Tool):
    """Список компонентов Blueprint"""
    
    name = "list_blueprint_components"
    description = "Возвращает список всех компонентов указанного Blueprint"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {
                "type": "string",
                "description": "Путь к Blueprint"
            }
        },
        "required": ["blueprint_path"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        
        script = f'''
import unreal
import json

def list_components():
    try:
        bp_path = "{bp_path}"
        
        blueprint = unreal.EditorAssetLibrary.load_asset(bp_path)
        if blueprint is None:
            return {{
                "success": False,
                "error": f"Blueprint не найден: {{bp_path}}",
                "message": "Проверьте путь к Blueprint"
            }}
        
        blueprint_class = blueprint.generated_class
        if blueprint_class is None:
            blueprint_class = blueprint.skeleton_generated_class
        
        components = blueprint_class.get_components_by_name()
        components_list = []
        
        for comp in components:
            comp_info = {{
                "name": comp.get_editor_property("name"),
                "class": comp.get_class().get_name(),
                "is_inherited": comp.get_editor_property("is_inherited_component")
            }}
            components_list.append(comp_info)
        
        return {{
            "success": True,
            "blueprint_path": bp_path,
            "components": components_list,
            "total_count": len(components_list),
            "message": f"Найдено {{len(components_list)}} компонентов"
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка получения списка компонентов: {{str(e)}}"
        }}

result = list_components()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "Список компонентов получен")
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
