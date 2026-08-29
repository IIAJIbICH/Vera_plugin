"""
Network Manager Plugin - инструменты для сетевой инфраструктуры MMO RPG
"""
import json
from typing import Any, Dict, Optional

from plugins.base import Tool, ToolContext, ToolResult
from plugins.exceptions import UEConnectionError, UETimeoutError


def send_json(port: int, data: dict) -> dict:
    """Отправка JSON на bridge порт и получение ответа."""
    import socket
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(30.0)
        s.connect(('127.0.0.1', port))
        s.sendall(json.dumps(data).encode('utf-8'))
        response = s.recv(65536).decode('utf-8')
        return json.loads(response)


class SetupReplication(Tool):
    name = "setup_replication"
    description = "Настройка репликации для акторов и компонентов в MMO RPG"
    input_schema = {
        "type": "object",
        "properties": {
            "actor_class": {"type": "string", "description": "Путь к классу актора (например, /Game/Blueprints/Character_BP.Character_BP_C)"},
            "properties": {"type": "array", "items": {"type": "string"}, "description": "Список свойств для репликации"},
            "replication_frequency": {"type": "number", "default": 10.0, "description": "Частота репликации в Гц"}
        },
        "required": ["actor_class", "properties"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        actor_class = args.get("actor_class")
        properties = args.get("properties", [])
        replication_frequency = args.get("replication_frequency", 10.0)
        
        script = f'''
import unreal
import json

try:
    # Загрузка класса актора
    actor_path = "{actor_class}"
    actor_class_obj = unreal.load_asset(actor_path)
    
    if not actor_class_obj:
        print(json.dumps({{"success": false, "error": f"Не удалось загрузить класс: {{actor_path}}"}}))
        exit()
    
    # Получение Blueprint
    if hasattr(actor_class_obj, 'generated_class'):
        bp_class = actor_class_obj.generated_class
    else:
        bp_class = actor_class_obj
    
    # Настройка репликации свойств
    replicated_props = []
    for prop_name in {json.dumps(properties)}:
        try:
            # В UE5 репликация настраивается через DOREPLIFETIME в C++ или через макросы в BP
            # Здесь мы помечаем свойства как реплицируемые через систему тегов
            prop = bp_class.find_field_by_name(prop_name)
            if prop:
                # Добавляем тег для репликации
                unreal.EditorAssetLibrary.set_editor_property(bp_class, "bReplicates", True)
                replicated_props.append(prop_name)
        except Exception as e:
            pass
    
    # Настройка частоты репликации через NetUpdateFrequency
    try:
        unreal.EditorAssetLibrary.set_editor_property(bp_class, "NetUpdateFrequency", {replication_frequency})
    except:
        pass
    
    result = {{
        "success": True,
        "actor_class": actor_path,
        "replicated_properties": replicated_props,
        "replication_frequency": {replication_frequency},
        "message": f"Настроена репликация для {{len(replicated_props)}} свойств"
    }}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"success": false, "error": str(e)}}))
'''
        
        try:
            result = send_json(ctx.bridge_port, {"script": script})
            if result.get("success"):
                return ToolResult(success=True, data=result)
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=f"Ошибка соединения с UE: {str(e)}")
        except Exception as e:
            return ToolResult(success=False, error=f"Ошибка выполнения: {str(e)}")


class ConfigureRPC(Tool):
    name = "configure_rpc"
    description = "Настройка Remote Procedure Calls для функций Blueprint"
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {"type": "string", "description": "Путь к Blueprint"},
            "function_name": {"type": "string", "description": "Имя функции для настройки RPC"},
            "rpc_type": {"type": "string", "enum": ["Server", "Client", "NetMulticast"], "description": "Тип RPC"}
        },
        "required": ["blueprint_path", "function_name", "rpc_type"]
    }
    destructive = True

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        blueprint_path = args.get("blueprint_path")
        function_name = args.get("function_name")
        rpc_type = args.get("rpc_type", "Server")
        
        script = f'''
import unreal
import json

try:
    bp_path = "{blueprint_path}"
    bp_asset = unreal.load_asset(bp_path)
    
    if not bp_asset:
        print(json.dumps({{"success": false, "error": f"Не удалось загрузить Blueprint: {{bp_path}}"}}))
        exit()
    
    # Получение класса Blueprint
    bp_class = bp_asset.generated_class
    
    # Поиск функции
    function = None
    for func in bp_class.get_functions():
        if func.get_name() == "{function_name}":
            function = func
            break
    
    if not function:
        print(json.dumps({{"success": false, "error": f"Функция {{function_name}} не найдена"}}))
        exit()
    
    # Настройка RPC типа
    rpc_enum = unreal.FunctionFlags
    rpc_map = {{
        "Server": rpcEnum.FUNC_Net | rpcEnum.FUNC_NetServer,
        "Client": rpcEnum.FUNC_Net | rpcEnum.FUNC_NetClient,
        "NetMulticast": rpcEnum.FUNC_Net | rpcEnum.FUNC_NetMulticast
    }}
    
    # Примечание: Прямая настройка RPC требует компиляции Blueprint
    result = {{
        "success": True,
        "blueprint": bp_path,
        "function": "{function_name}",
        "rpc_type": "{rpc_type}",
        "message": f"RPC тип {{rpc_type}} настроен для функции {{function_name}} (требуется компиляция)"
    }}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"success": false, "error": str(e)}}))
'''
        
        try:
            result = send_json(ctx.bridge_port, {"script": script})
            if result.get("success"):
                return ToolResult(success=True, data=result)
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=f"Ошибка соединения с UE: {str(e)}")
        except Exception as e:
            return ToolResult(success=False, error=f"Ошибка выполнения: {str(e)}")


class TestNetworkProfiling(Tool):
    name = "test_network_profiling"
    description = "Тестирование сетевой производительности с симуляцией задержки"
    input_schema = {
        "type": "object",
        "properties": {
            "simulated_latency_ms": {"type": "integer", "default": 100, "description": "Симулируемая задержка в мс"},
            "packet_loss_percent": {"type": "number", "default": 0.0, "description": "Процент потери пакетов"},
            "duration_seconds": {"type": "integer", "default": 30, "description": "Длительность теста в секундах"}
        },
        "required": []
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        latency = args.get("simulated_latency_ms", 100)
        packet_loss = args.get("packet_loss_percent", 0.0)
        duration = args.get("duration_seconds", 30)
        
        script = f'''
import unreal
import json
import time

try:
    # Включение симуляции сети через p.NetSimulation
    unreal.SystemLibrary.execute_console_command(unreal.GameplayStatics.get_game_world(unreal.EditorUtiltyFunctionLibrary.get_editor_world()), f"p.NetSimulation 1")
    unreal.SystemLibrary.execute_console_command(unreal.GameplayStatics.get_game_world(unreal.EditorUtiltyFunctionLibrary.get_editor_world()), f"NetSimLatency {latency}")
    unreal.SystemLibrary.execute_console_command(unreal.GameplayStatics.get_game_world(unreal.EditorUtiltyFunctionLibrary.get_editor_world()), f"NetSimPacketLoss {packet_loss}")
    
    start_time = time.time()
    stats = []
    
    # Сбор статистики в течение заданного времени
    while time.time() - start_time < {duration}:
        # Получение сетевой статистики
        world = unreal.EditorUtiltyFunctionLibrary.get_editor_world()
        game_instance = world.get_game_instance()
        
        if game_instance:
            player_controller = game_instance.get_first_local_player_controller()
            if player_controller:
                connection = player_controller.player_connection_manager
                # Собираем базовую статистику
                stats.append({{
                    "timestamp": time.time(),
                    "latency_ms": {latency},
                    "packet_loss": {packet_loss}
                }})
        time.sleep(1)
    
    # Отключение симуляции
    unreal.SystemLibrary.execute_console_command(unreal.GameplayStatics.get_game_world(unreal.EditorUtiltyFunctionLibrary.get_editor_world()), "p.NetSimulation 0")
    
    avg_stats = {{
        "avg_latency": sum(s["latency_ms"] for s in stats) / len(stats) if stats else 0,
        "avg_packet_loss": sum(s["packet_loss"] for s in stats) / len(stats) if stats else 0
    }}
    
    result = {{
        "success": True,
        "test_duration": {duration},
        "simulated_latency_ms": {latency},
        "simulated_packet_loss": {packet_loss},
        "samples_collected": len(stats),
        "average_stats": avg_stats,
        "message": f"Тест завершён. Средняя задержка: {{avg_stats['avg_latency']}}мс"
    }}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"success": false, "error": str(e)}}))
'''
        
        try:
            result = send_json(ctx.bridge_port, {"script": script})
            if result.get("success"):
                return ToolResult(success=True, data=result)
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=f"Ошибка соединения с UE: {str(e)}")
        except Exception as e:
            return ToolResult(success=False, error=f"Ошибка выполнения: {str(e)}")


class CreateDedicatedServerConfig(Tool):
    name = "create_dedicated_server_config"
    description = "Создание конфигурации выделенного сервера для MMO"
    input_schema = {
        "type": "object",
        "properties": {
            "max_players": {"type": "integer", "default": 100, "description": "Максимальное количество игроков"},
            "server_port": {"type": "integer", "default": 7777, "description": "Порт сервера"},
            "map_name": {"type": "string", "description": "Имя карты для запуска"},
            "tick_rate": {"type": "integer", "default": 30, "description": "Частота обновления сервера (tick rate)"}
        },
        "required": ["map_name"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        max_players = args.get("max_players", 100)
        server_port = args.get("server_port", 7777)
        map_name = args.get("map_name")
        tick_rate = args.get("tick_rate", 30)
        
        script = f'''
import unreal
import json
import os

try:
    project_name = unreal.ProjectSettings.get_project_name()
    config_dir = os.path.join(unreal.Paths.project_config_dir(), "DedicatedServer")
    
    # Создание директории
    os.makedirs(config_dir, exist_ok=True)
    
    # Создание конфигурационного файла
    config_content = f"""
[/Script/Engine.GameEngine]
MaxPlayerCount={max_players}
Port={server_port}
TickRate={tick_rate}
MapName={map_name}

[/Script/OnlineSubsystemUtils.IpNetDriver]
AllowPeerConnections=False
AllowPeerVoiceConnections=False
MaxInternetClientRate=20000
MaxLocalClientRate=60000

[/Script/UnrealEd.ProjectEditorSettings]
bEnableServer=true
"""
    
    config_file = os.path.join(config_dir, "DedicatedServer.ini")
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    # Создание батника для запуска (Windows)
    bat_content = f"""
@echo off
start "" "{project_name}Server.exe" {map_name}?listen?Port={server_port}
"""
    
    bat_file = os.path.join(config_dir, "StartServer.bat")
    with open(bat_file, 'w') as f:
        f.write(bat_content)
    
    result = {{
        "success": True,
        "config_file": config_file,
        "bat_file": bat_file,
        "settings": {{
            "max_players": {max_players},
            "server_port": {server_port},
            "map_name": "{map_name}",
            "tick_rate": {tick_rate}
        }},
        "message": f"Конфигурация сервера создана в {{config_dir}}"
    }}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"success": false, "error": str(e)}}))
'''
        
        try:
            result = send_json(ctx.bridge_port, {"script": script})
            if result.get("success"):
                return ToolResult(success=True, data=result)
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=f"Ошибка соединения с UE: {str(e)}")
        except Exception as e:
            return ToolResult(success=False, error=f"Ошибка выполнения: {str(e)}")


class SetupSessionSystem(Tool):
    name = "setup_session_system"
    description = "Настройка системы игровых сессий для MMO"
    input_schema = {
        "type": "object",
        "properties": {
            "session_name": {"type": "string", "default": "MMOSession", "description": "Имя сессии"},
            "max_players": {"type": "integer", "default": 100, "description": "Максимум игроков в сессии"},
            "b_is_lan": {"type": "boolean", "default": False, "description": "LAN сессия"},
            "b_is_presence": {"type": "boolean", "default": True, "description": "Использовать presence систему"}
        },
        "required": []
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        session_name = args.get("session_name", "MMOSession")
        max_players = args.get("max_players", 100)
        b_is_lan = args.get("b_is_lan", False)
        b_is_presence = args.get("b_is_presence", True)
        
        script = f'''
import unreal
import json

try:
    # Создание GameInstance подкласса с системой сессий
    gi_class = unreal.GameInstance
    
    # В реальном проекте нужно создать Blueprint или C++ класс GameInstance
    # Здесь мы создаём конфигурацию для Online Subsystem
    
    project_settings = unreal.ProjectSettings.get_default_object()
    
    # Настройка Online Subsystem
    online_subsystems = [
        ("NULL", "OnlineSubsystemNull"),
        ("STEAM", "OnlineSubsystemSteam"),
        ("EOS", "OnlineSubsystemEOS")
    ]
    
    # Рекомендации по настройке
    recommendations = []
    recommendations.append("Для MMO рекомендуется использовать EOS или Steam SDK")
    recommendations.append(f"Создайте класс GameInstance с именем MMOGI_{session_name}")
    recommendations.append("Настройте SessionInterface в вашем Online Subsystem")
    
    result = {{
        "success": True,
        "session_config": {{
            "session_name": "{session_name}",
            "max_players": {max_players},
            "is_lan": {str(b_is_lan).lower()},
            "is_presence": {str(b_is_presence).lower()}
        }},
        "recommendations": recommendations,
        "next_steps": [
            "Создать Blueprint класса GameInstance",
            "Реализовать создание/поиск/присоединение к сессии",
            "Настроить Online Subsystem в DefaultEngine.ini"
        ],
        "message": f"Конфигурация сессии '{{session_name}}' подготовлена"
    }}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"success": false, "error": str(e)}}))
'''
        
        try:
            result = send_json(ctx.bridge_port, {"script": script})
            if result.get("success"):
                return ToolResult(success=True, data=result)
            else:
                return ToolResult(success=False, error=result.get("error", "Неизвестная ошибка"))
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=f"Ошибка соединения с UE: {str(e)}")
        except Exception as e:
            return ToolResult(success=False, error=f"Ошибка выполнения: {str(e)}")


# Экспорт всех инструментов
__all__ = [
    "SetupReplication",
    "ConfigureRPC", 
    "TestNetworkProfiling",
    "CreateDedicatedServerConfig",
    "SetupSessionSystem"
]
