"""
Dependency Manager - Управление зависимостями ассетов
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


class FindAssetDependenciesTool(Tool):
    name = "find_asset_dependencies"
    description = "Находит все зависимости указанного ассета"
    destructive = False
    
    input_schema = {"type": "object", "properties": {"asset_path": {"type": "string"}}, "required": ["asset_path"]}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        asset_path = args.get("asset_path")
        
        script = f'''
import unreal
import json

def find_deps():
    try:
        asset_path = "{asset_path}"
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not asset:
            return {{"success": False, "error": "Ассет не найден"}}
        
        deps = unreal.EditorAssetLibrary.find_dependency_package_names(asset_path)
        
        return {{"success": True, "dependencies": list(deps), "count": len(deps)}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(find_deps()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class FindReferencersTool(Tool):
    name = "find_referencers"
    description = "Находит все ассеты, ссылающиеся на указанный"
    destructive = False
    
    input_schema = {"type": "object", "properties": {"asset_path": {"type": "string"}}, "required": ["asset_path"]}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        asset_path = args.get("asset_path")
        
        script = f'''
import unreal
import json

def find_refs():
    try:
        asset_path = "{asset_path}"
        refs = unreal.EditorAssetLibrary.find_referencing_assets(asset_path)
        return {{"success": True, "referencers": refs, "count": len(refs)}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(find_refs()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class FindUnusedAssetsTool(Tool):
    name = "find_unused_assets"
    description = "Ищет неиспользуемые ассеты в проекте"
    destructive = False
    
    input_schema = {"type": "object", "properties": {"limit": {"type": "integer", "default": 100}}}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        limit = args.get("limit", 100)
        
        script = f'''
import unreal
import json

def find_unused():
    try:
        limit = {limit}
        unused = []
        
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        all_assets = registry.get_all_assets()
        
        for asset in all_assets[:500]:
            path = asset.package_name + "/" + asset.asset_name
            refs = unreal.EditorAssetLibrary.find_referencing_assets(path)
            
            # Исключаем системные ассеты
            if len(refs) == 0 and "/Game/" in path:
                unused.append(path)
                if len(unused) >= limit:
                    break
        
        return {{"success": True, "unused_assets": unused, "count": len(unused)}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(find_unused()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class AnalyzeLoadTimeTool(Tool):
    name = "analyze_load_time"
    description = "Оценивает время загрузки ассета"
    destructive = False
    
    input_schema = {"type": "object", "properties": {"asset_path": {"type": "string"}}, "required": ["asset_path"]}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        asset_path = args.get("asset_path")
        
        script = f'''
import unreal
import json
import time

def analyze_load():
    try:
        asset_path = "{asset_path}"
        
        start = time.time()
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        load_time = time.time() - start
        
        size = asset.get_resource_size() if asset else 0
        
        rating = "fast"
        if load_time > 0.5: rating = "medium"
        if load_time > 1.0: rating = "slow"
        
        return {{"success": True, "load_time_ms": round(load_time * 1000, 2), "size_bytes": size, "rating": rating}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(analyze_load()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))
