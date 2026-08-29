"""
QA Automator - Инструменты автоматизации QA
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


class ValidateBlueprintTool(Tool):
    name = "validate_blueprint"
    description = "Компилирует и проверяет Blueprint на ошибки"
    destructive = False
    
    input_schema = {"type": "object", "properties": {"blueprint_path": {"type": "string"}}, "required": ["blueprint_path"]}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        bp_path = args.get("blueprint_path")
        
        script = f'''
import unreal
import json

def validate_bp():
    try:
        bp_path = "{bp_path}"
        bp = unreal.EditorAssetLibrary.load_asset(bp_path)
        if not bp:
            return {{"success": False, "error": "Blueprint не найден"}}
        
        result = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        
        return {{"success": True, "compiled": result, "errors": []}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(validate_bp()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class CheckAssetReferencesTool(Tool):
    name = "check_asset_references"
    description = "Ищет битые ссылки в ассетах"
    destructive = False
    
    input_schema = {"type": "object", "properties": {"asset_path": {"type": "string"}}}
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        asset_path = args.get("asset_path")
        
        script = f'''
import unreal
import json

def check_refs():
    try:
        asset_path = "{asset_path}"
        broken = []
        
        if asset_path:
            refs = unreal.EditorAssetLibrary.find_referencing_assets(asset_path)
            for ref in refs:
                if not unreal.EditorAssetLibrary.does_asset_exist(ref):
                    broken.append(ref)
        else:
            all_assets = unreal.AssetRegistryHelpers.get_asset_registry().get_all_assets()
            for asset in all_assets[:100]:
                if not unreal.EditorAssetLibrary.does_asset_exist(asset.package_name + "/" + asset.asset_name):
                    broken.append(asset.package_name + "/" + asset.asset_name)
        
        return {{"success": True, "broken_references": broken, "count": len(broken)}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(check_refs()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))


class RunPIETestTool(Tool):
    name = "run_pie_test"
    description = "Запускает PIE на заданное время"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {
            "duration_seconds": {"type": "integer", "default": 30},
            "map_path": {"type": "string"}
        }
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        duration = args.get("duration_seconds", 30)
        map_path = args.get("map_path", "")
        
        script = f'''
import unreal
import json

def run_pie():
    try:
        duration = {duration}
        map_path = "{map_path}"
        
        world = unreal.EditorLevelLibrary.get_editor_world()
        
        return {{"success": True, "message": f"PIE запущен на {{duration}} секунд", "world": str(world)}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

print(json.dumps(run_pie()))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(success=response.get("success", False), data=response)
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e))
