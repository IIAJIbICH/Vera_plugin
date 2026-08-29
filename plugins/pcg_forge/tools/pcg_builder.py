"""
PCG Forge - Создание и настройка PCG графов
"""

import json
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


class BuildPCGGraphTool(Tool):
    """Создание PCG графа с нодами"""
    
    name = "build_pcg_graph"
    description = "Добавляет ноды в PCG граф для процедурной генерации (LandscapeData, SurfaceSampler, Spawner)"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "graph_name": {
                "type": "string",
                "description": "Имя PCG графа"
            },
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["LandscapeData", "SurfaceSampler", "Spawner", 
                                     "Transform", "Filter", "PoissonDisc", "DensityFilter"]
                        },
                        "name": {"type": "string"},
                        "settings": {"type": "object"}
                    }
                },
                "description": "Список нод для добавления"
            }
        },
        "required": ["graph_name", "nodes"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        graph_name = args.get("graph_name")
        nodes = args.get("nodes", [])
        
        script = f'''
import unreal
import json

def build_pcg_graph():
    try:
        graph_name = "{graph_name}"
        nodes_config = {json.dumps(nodes)}
        
        # Создаём PCG Graph Asset
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        package_path = "/Game/PCG"
        
        if not unreal.EditorAssetLibrary.does_directory_exist(package_path):
            unreal.EditorAssetLibrary.make_directory(package_path)
        
        # Создаём график
        pcg_graph = unreal.PCGGraph()
        pcg_graph.set_editor_property("graph_name", graph_name)
        
        nodes_added = 0
        graph_nodes = []
        
        for node_config in nodes_config:
            node_type = node_config.get("type", "SurfaceSampler")
            node_name = node_config.get("name", node_type)
            settings = node_config.get("settings", {{}})
            
            # Создаём ноду соответствующего типа
            pcg_node = unreal.PCGNode()
            
            # Выбираем элемент графа по типу
            if node_type == "LandscapeData":
                graph_element = unreal.PCGLandscapeDataSettings()
            elif node_type == "SurfaceSampler":
                graph_element = unreal.PCGSurfaceSamplerSettings()
            elif node_type == "Spawner":
                graph_element = unreal.PCGSpawnerSettings()
            elif node_type == "Transform":
                graph_element = unreal.PCGTransformSettings()
            elif node_type == "Filter":
                graph_element = unreal.PCGFilterSettings()
            elif node_type == "PoissonDisc":
                graph_element = unreal.PCGPoissonDiscSettings()
            else:
                graph_element = unreal.PCGSurfaceSamplerSettings()
            
            pcg_node.set_editor_property("node_settings", graph_element)
            pcg_node.set_editor_property("title", node_name)
            
            graph_nodes.append(pcg_node)
            nodes_added += 1
        
        # Добавляем ноды в граф
        pcg_graph.set_editor_property("nodes", graph_nodes)
        
        # Сохраняем
        asset_tools.register_asset(pcg_graph, package_path)
        unreal.EditorAssetLibrary.save_loaded_asset(pcg_graph)
        
        return {{
            "success": True,
            "graph_path": f"{{package_path}}/{{graph_name}}",
            "nodes_added": nodes_added,
            "message": f"PCG граф '{{graph_name}}' создан с {{nodes_added}} нодами"
        }}
        
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "message": f"Ошибка создания PCG графа: {{str(e)}}"
        }}

result = build_pcg_graph()
print(json.dumps(result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=response.get("message", "PCG граф создан")
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
