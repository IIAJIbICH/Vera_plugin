"""
Smart Refactor - Инструменты рефакторинга
"""

import json
from ..base import Tool, ToolResult, ToolContext
from ..exceptions import UEConnectionError, UETimeoutError


def send_json(bridge_port: int, data: dict) -> dict:
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
        raise UETimeoutError("Превышено время ожидания")
    except Exception as e:
        raise UEConnectionError(f"Ошибка соединения: {e}")


class RenameAssetSafeTool(Tool):
    name = "rename_asset_safe"
    description = "Переименовывает ассет с обновлением всех ссылок"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "asset_path": {"type": "string", "description": "Путь к ассету"},
            "new_name": {"type": "string", "description": "Новое имя"}
        },
        "required": ["asset_path", "new_name"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        asset_path = args.get("asset_path")
        new_name = args.get("new_name")
        
        script = f'''
import unreal
import json

def rename_asset():
    try:
        asset_path = "{asset_path}"
        new_name = "{new_name}"
        
        asset_data = unreal.EditorAssetLibrary.find_asset_data(asset_path)
        if not asset_data:
            return {{"success": False, "error": "Ассет не найден"}}
        
        package_path = asset_data.package_name.rsplit("/", 1)[0]
        new_path = f"{{package_path}}/{{new_name}}"
        
        result = unreal.EditorAssetLibrary.rename_loaded_asset(asset_data.asset, new_name)
        
        return {{"success": True, "old_path": asset_path, "new_path": new_path}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(rename_asset()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response, 
                            message="Ассет переименован" if response.get("success") else response.get("error"))
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class FindDuplicateAssetsTool(Tool):
    name = "find_duplicate_assets"
    description = "Ищет дубликаты ассетов"
    destructive = False
    
    input_schema = {"type": "object", "properties": {"project_path": {"type": "string"}}}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        # Упрощённая реализация через файловую систему
        import os
        from pathlib import Path
        import hashlib
        
        project_path = args.get("project_path", ctx.project_path)
        content_path = os.path.join(project_path, "Content")
        
        hashes = {}
        duplicates = []
        
        for ext in ["*.uasset", "*.umap"]:
            for f in Path(content_path).rglob(ext):
                try:
                    h = hashlib.md5(open(f, 'rb').read(8192)).hexdigest()
                    if h in hashes:
                        duplicates.append({"original": hashes[h], "duplicate": str(f)})
                    else:
                        hashes[h] = str(f)
                except: pass
        
        return ToolResult(success=True, data={"duplicates": duplicates, "count": len(duplicates)},
                         message=f"Найдено {len(duplicates)} дубликатов")


class AnalyzeBlueprintComplexityTool(Tool):
    name = "analyze_blueprint_complexity"
    description = "Анализирует сложность Blueprint"
    destructive = False
    
    input_schema = {"type": "object", "properties": {"blueprint_path": {"type": "string"}}, "required": ["blueprint_path"]}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        
        script = f'''
import unreal
import json

def analyze_bp():
    try:
        bp_path = "{bp_path}"
        bp = unreal.EditorAssetLibrary.load_asset(bp_path)
        if not bp:
            return {{"success": False, "error": "Blueprint не найден"}}
        
        graph = bp.event_graph
        nodes = graph.nodes if graph else []
        
        complexity = "low"
        if len(nodes) > 50: complexity = "medium"
        if len(nodes) > 200: complexity = "high"
        
        return {{"success": True, "node_count": len(nodes), "complexity": complexity}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(analyze_bp()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class SuggestOptimizationTool(Tool):
    name = "suggest_optimization"
    description = "Даёт рекомендации по оптимизации"
    destructive = False
    
    input_schema = {"type": "object", "properties": {}}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        recommendations = [
            {"area": "Textures", "recommendation": "Используйте сжатие BC7 для мобильных"},
            {"area": "Blueprints", "recommendation": "Избегайте Event Tick в производственных классах"},
            {"area": "Materials", "recommendation": "Объединяйте материалы с одинаковыми свойствами"},
            {"area": "Lighting", "recommendation": "Используйте запечённое освещение где возможно"}
        ]
        return ToolResult(success=True, data={"recommendations": recommendations}, 
                         message=f"Сгенерировано {len(recommendations)} рекомендаций")
