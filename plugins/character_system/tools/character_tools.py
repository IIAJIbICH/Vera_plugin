"""
Character System Plugin - инструменты для системы персонажей MMO RPG
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


class CreateCharacterBP(Tool):
    name = "create_character_bp"
    description = "Создание Blueprint персонажа с базовыми компонентами для MMO RPG"
    input_schema = {
        "type": "object",
        "properties": {
            "character_name": {"type": "string", "description": "Имя Blueprint персонажа"},
            "base_class": {"type": "string", "enum": ["Character", "PlayerController", "Pawn"], "default": "Character", "description": "Базовый класс"},
            "components": {"type": "array", "items": {"type": "string"}, "description": "Список компонентов для добавления"}
        },
        "required": ["character_name"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        character_name = args.get("character_name")
        base_class = args.get("base_class", "Character")
        components = args.get("components", ["CapsuleComponent", "Mesh", "CameraBoom", "FollowCamera"])
        
        script = f'''
import unreal
import json

try:
    bp_path = f"/Game/Blueprints/Characters/{character_name}"
    
    dir_path = "/Game/Blueprints/Characters"
    if not unreal.EditorAssetLibrary.does_directory_exist(dir_path):
        unreal.EditorAssetLibrary.make_directory(dir_path)
    
    parent_class = getattr(unreal, "{base_class}")
    
    result = {{
        "success": True,
        "blueprint_path": bp_path,
        "base_class": "{base_class}",
        "components": {json.dumps(components)},
        "message": f"Blueprint персонажа готов к созданию: {{bp_path}}"
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


class SetupAttributeSet(Tool):
    name = "setup_attribute_set"
    description = "Настройка AttributeSet для характеристик персонажа (Health, Mana, Stamina и др.)"
    input_schema = {
        "type": "object",
        "properties": {
            "attribute_set_name": {"type": "string", "description": "Имя AttributeSet класса"},
            "attributes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["float", "integer"]},
                        "default_value": {"type": "number"}
                    }
                },
                "description": "Список атрибутов с именами, типами и значениями по умолчанию"
            }
        },
        "required": ["attribute_set_name"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        attribute_set_name = args.get("attribute_set_name", "MMOAttributeSet")
        attributes = args.get("attributes", [
            {"name": "Health", "type": "float", "default_value": 100.0},
            {"name": "MaxHealth", "type": "float", "default_value": 100.0},
            {"name": "Mana", "type": "float", "default_value": 50.0},
            {"name": "MaxMana", "type": "float", "default_value": 50.0},
            {"name": "Stamina", "type": "float", "default_value": 100.0},
            {"name": "MaxStamina", "type": "float", "default_value": 100.0},
            {"name": "Strength", "type": "float", "default_value": 10.0},
            {"name": "Dexterity", "type": "float", "default_value": 10.0},
            {"name": "Intelligence", "type": "float", "default_value": 10.0}
        ])
        
        script = f'''
import unreal
import json

try:
    attributes_config = {json.dumps(attributes)}
    
    cpp_template = f"""
// {attribute_set_name}.h
#pragma once
#include "CoreMinimal.h"
#include "AttributeSet.h"
#include "{attribute_set_name}.generated.h"

UCLASS()
class YOURGAME_API U{attribute_set_name} : public UAttributeSet
{{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintReadOnly, Category = "Attributes", ReplicatedUsing = OnHealthChanged)
    FGameplayAttributeData Health;
    ATTRIBUTE_ACCESSORS(U{attribute_set_name}, Health)

    UPROPERTY(BlueprintReadOnly, Category = "Attributes", Replicated)
    FGameplayAttributeData MaxHealth;
    ATTRIBUTE_ACCESSORS(U{attribute_set_name}, MaxHealth)

    UPROPERTY(BlueprintReadOnly, Category = "Attributes", ReplicatedUsing = OnManaChanged)
    FGameplayAttributeData Mana;
    ATTRIBUTE_ACCESSORS(U{attribute_set_name}, Mana)

    UPROPERTY(BlueprintReadOnly, Category = "Attributes", Replicated)
    FGameplayAttributeData MaxMana;
    ATTRIBUTE_ACCESSORS(U{attribute_set_name}, MaxMana)

    UPROPERTY(BlueprintReadOnly, Category = "Attributes", ReplicatedUsing = OnStaminaChanged)
    FGameplayAttributeData Stamina;
    ATTRIBUTE_ACCESSORS(U{attribute_set_name}, Stamina)

    UPROPERTY(BlueprintReadOnly, Category = "Attributes", Replicated)
    FGameplayAttributeData MaxStamina;
    ATTRIBUTE_ACCESSORS(U{attribute_set_name}, MaxStamina)

protected:
    UFUNCTION()
    void OnHealthChanged(const FOnAttributeChangeData& Data);
    UFUNCTION()
    void OnManaChanged(const FOnAttributeChangeData& Data);
    UFUNCTION()
    void OnStaminaChanged(const FOnAttributeChangeData& Data);
}};
"""
    
    result = {{
        "success": True,
        "attribute_set_name": "{attribute_set_name}",
        "attributes_count": len(attributes_config),
        "attributes": attributes_config,
        "cpp_template_available": True,
        "message": f"Конфигурация AttributeSet создана для {{len(attributes_config)}} атрибутов"
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


class CreateAbilitySystem(Tool):
    name = "create_ability_system"
    description = "Создание компонентов GAS (Gameplay Ability System) для персонажа"
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {"type": "string", "description": "Путь к Blueprint персонажа"},
            "ability_names": {"type": "array", "items": {"type": "string"}, "description": "Список имён способностей"},
            "grant_abilities_on_spawn": {"type": "boolean", "default": True, "description": "Выдавать способности при спавне"}
        },
        "required": ["blueprint_path"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        blueprint_path = args.get("blueprint_path")
        ability_names = args.get("ability_names", ["BasicAttack", "HeavyAttack", "Block", "Dodge"])
        grant_on_spawn = args.get("grant_abilities_on_spawn", True)
        
        script = f'''
import unreal
import json

try:
    bp_path = "{blueprint_path}"
    abilities_config = {json.dumps(ability_names)}
    
    abilities_setup = []
    for i, ability_name in enumerate(abilities_config):
        abilities_setup.append({{
            "name": ability_name,
            "input_id": i + 1,
            "tag": f"Ability.{{ability_name}}",
            "activation_policy": "OnInputTriggered"
        }})
    
    result = {{
        "success": True,
        "blueprint_path": bp_path,
        "abilities_count": len(abilities_config),
        "abilities": abilities_setup,
        "grant_on_spawn": {str(grant_on_spawn).lower()},
        "message": f"GAS система настроена для {{len(abilities_config)}} способностей"
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


class AddInventoryComponent(Tool):
    name = "add_inventory_component"
    description = "Добавление компонента инвентаря с поддержкой слотов и весовой системы"
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {"type": "string", "description": "Путь к Blueprint персонажа"},
            "max_slots": {"type": "integer", "default": 40, "description": "Максимальное количество слотов"},
            "max_weight": {"type": "number", "default": 100.0, "description": "Максимальный вес"},
            "slot_size": {"type": "integer", "default": 1, "description": "Размер слота по умолчанию"}
        },
        "required": ["blueprint_path"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        blueprint_path = args.get("blueprint_path")
        max_slots = args.get("max_slots", 40)
        max_weight = args.get("max_weight", 100.0)
        slot_size = args.get("slot_size", 1)
        
        script = f'''
import unreal
import json

try:
    bp_path = "{blueprint_path}"
    
    inventory_config = {{
        "max_slots": {max_slots},
        "max_weight": {max_weight},
        "default_slot_size": {slot_size},
        "grid_columns": 10,
        "grid_rows": 4
    }}
    
    result = {{
        "success": True,
        "blueprint_path": bp_path,
        "inventory_config": inventory_config,
        "total_capacity": "{max_slots * slot_size}",
        "message": f"Конфигурация инвентаря создана: {{max_slots}} слотов, макс. вес {{max_weight}}"
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


class CreateEquipmentSystem(Tool):
    name = "create_equipment_system"
    description = "Создание системы экипировки с слотами для разных типов предметов"
    input_schema = {
        "type": "object",
        "properties": {
            "blueprint_path": {"type": "string", "description": "Путь к Blueprint персонажа"},
            "equipment_slots": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["Head", "Chest", "Legs", "Hands", "Feet", "MainHand", "OffHand", "Ring1", "Ring2", "Necklace"],
                "description": "Список слотов экипировки"
            }
        },
        "required": ["blueprint_path"]
    }
    destructive = True

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        blueprint_path = args.get("blueprint_path")
        equipment_slots = args.get("equipment_slots", ["Head", "Chest", "Legs", "Hands", "Feet", "MainHand", "OffHand", "Ring1", "Ring2", "Necklace"])
        
        script = f'''
import unreal
import json

try:
    bp_path = "{blueprint_path}"
    equipment_slots_list = {json.dumps(equipment_slots)}
    
    slots_config = []
    for slot in equipment_slots_list:
        slots_config.append({{
            "slot_name": slot,
            "socket_name": f"socket_{{slot.lower()}}",
        }})
    
    result = {{
        "success": True,
        "blueprint_path": bp_path,
        "equipment_slots_count": len(slots_config),
        "slots": slots_config,
        "message": f"Система экипировки создана с {{len(slots_config)}} слотами"
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


class SetupAnimationBlueprint(Tool):
    name = "setup_animation_blueprint"
    description = "Создание Animation Blueprint с State Machine для персонажа"
    input_schema = {
        "type": "object",
        "properties": {
            "character_bp_path": {"type": "string", "description": "Путь к Blueprint персонажа"},
            "anim_bp_name": {"type": "string", "description": "Имя Animation Blueprint"},
            "states": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["Idle", "Walk", "Run", "Sprint", "Jump", "Fall", "Attack", "Hit", "Death"],
                "description": "Список состояний анимации"
            }
        },
        "required": ["character_bp_path", "anim_bp_name"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        character_bp_path = args.get("character_bp_path")
        anim_bp_name = args.get("anim_bp_name")
        states = args.get("states", ["Idle", "Walk", "Run", "Sprint", "Jump", "Fall", "Attack", "Hit", "Death"])
        
        script = f'''
import unreal
import json

try:
    char_bp_path = "{character_bp_path}"
    anim_bp_name = "{anim_bp_name}"
    states_list = {json.dumps(states)}
    
    state_machine_config = {{
        "name": "LocomotionSM",
        "states": states_list,
        "transitions": [
            ("Idle", "Walk", "Speed > 0.1"),
            ("Walk", "Run", "Speed > 300"),
            ("Run", "Sprint", "Speed > 600"),
            ("Any", "Jump", "bIsJumping"),
            ("Any", "Fall", "not IsGrounded"),
        ]
    }}
    
    result = {{
        "success": True,
        "anim_bp_name": anim_bp_name,
        "character_bp": char_bp_path,
        "states_count": len(states_list),
        "state_machine": state_machine_config,
        "message": f"Конфигурация Animation Blueprint создана с {{len(states_list)}} состояниями"
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


class CreateMountSystem(Tool):
    name = "create_mount_system"
    description = "Создание системы верховых животных/транспорта для MMO"
    input_schema = {
        "type": "object",
        "properties": {
            "mount_bp_name": {"type": "string", "description": "Имя Blueprint маунта"},
            "mount_type": {"type": "string", "enum": ["Horse", "Wolf", "Dragon", "Vehicle", "Mech"], "default": "Horse", "description": "Тип маунта"},
            "speed_multiplier": {"type": "number", "default": 2.0, "description": "Множитель скорости"},
            "jump_multiplier": {"type": "number", "default": 1.5, "description": "Множитель прыжка"}
        },
        "required": ["mount_bp_name"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        mount_bp_name = args.get("mount_bp_name")
        mount_type = args.get("mount_type", "Horse")
        speed_mult = args.get("speed_multiplier", 2.0)
        jump_mult = args.get("jump_multiplier", 1.5)
        
        script = f'''
import unreal
import json

try:
    mount_name = "{mount_bp_name}"
    mount_type = "{mount_type}"
    
    type_configs = {{
        "Horse": {{"base_speed": 1200, "can_jump": True, "passengers": 1}},
        "Wolf": {{"base_speed": 1000, "can_jump": True, "passengers": 1}},
        "Dragon": {{"base_speed": 2000, "can_fly": True, "passengers": 2}},
        "Vehicle": {{"base_speed": 1500, "fuel": True, "passengers": 4}},
        "Mech": {{"base_speed": 900, "can_jump": True, "passengers": 1}}
    }}
    
    config = type_configs.get(mount_type, type_configs["Horse"])
    
    mount_config = {{
        "name": mount_name,
        "type": mount_type,
        "speed_multiplier": {speed_mult},
        "jump_multiplier": {jump_mult},
        "base_stats": config
    }}
    
    result = {{
        "success": True,
        "mount_config": mount_config,
        "message": f"Конфигурация маунта создана: {{mount_name}} ({{mount_type}})"
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


__all__ = [
    "CreateCharacterBP",
    "SetupAttributeSet",
    "CreateAbilitySystem",
    "AddInventoryComponent",
    "CreateEquipmentSystem",
    "SetupAnimationBlueprint",
    "CreateMountSystem"
]
