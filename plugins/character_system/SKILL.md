# Character System Plugin

## Описание
Плагин для создания системы персонажей MMO RPG в Unreal Engine 5.7 с использованием GAS (Gameplay Ability System).

## Инструменты

### create_character_bp
Создание Blueprint персонажа с базовыми компонентами.
- **destructive**: false
- **Параметры**: character_name, base_class (Character/PlayerController), components (список)

### setup_attribute_set
Настройка AttributeSet для характеристик персонажа (Health, Mana, Stamina, Strength, Dexterity, Intelligence).
- **destructive**: false
- **Параметры**: attribute_set_name, attributes (список с типами и значениями по умолчанию)

### create_ability_system
Создание компонентов GAS: AbilitySystemComponent, GamepadAbilitySystemComponent.
- **destructive**: false
- **Параметры**: blueprint_path, ability_names (список), grant_abilities_on_spawn

### add_inventory_component
Добавление компонента инвентаря с поддержкой слотов и весовой системы.
- **destructive**: false
- **Параметры**: blueprint_path, max_slots, max_weight, slot_size

### create_equipment_system
Создание системы экипировки с слотами для разных типов предметов.
- **destructive**: true
- **Параметры**: blueprint_path, equipment_slots (Head, Chest, Legs, Hands, Feet, Weapon, Shield, Ring, Necklace)

### setup_animation_blueprint
Создание Animation Blueprint с State Machine для персонажа.
- **destructive**: false
- **Параметры**: character_bp_path, anim_bp_name, states (Idle, Walk, Run, Jump, Attack, Death)

### create_mount_system
Создание системы верховых животных/транспорта.
- **destructive**: false
- **Параметры**: mount_bp_name, mount_type (Horse, Wolf, Dragon, Vehicle), speed_multiplier, jump_multiplier

## Использование
```json
{
  "tool": "create_character_bp",
  "args": {
    "character_name": "MMOCharacter",
    "base_class": "Character",
    "components": ["CapsuleComponent", "Mesh", "CameraBoom", "FollowCamera"]
  }
}
```
