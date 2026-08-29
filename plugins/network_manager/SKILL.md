# Network Manager Plugin

## Описание
Плагин для настройки сетевой инфраструктуры MMO RPG в Unreal Engine 5.7.

## Инструменты

### setup_replication
Настройка репликации для акторов и компонентов.
- **destructive**: false
- **Параметры**: actor_class, properties (список), replication_frequency

### configure_rpc
Настройка Remote Procedure Calls для функций Blueprint.
- **destructive**: true
- **Параметры**: blueprint_path, function_name, rpc_type (Server, Client, NetMulticast)

### test_network_profiling
Тестирование сетевой производительности с симуляцией задержки.
- **destructive**: false
- **Параметры**: simulated_latency_ms, packet_loss_percent, duration_seconds

### create_dedicated_server_config
Создание конфигурации выделенного сервера.
- **destructive**: false
- **Параметры**: max_players, server_port, map_name, tick_rate

### setup_session_system
Настройка системы игровых сессий.
- **destructive**: false
- **Параметры**: session_name, max_players, b_is_lan, b_is_presence

## Использование
```json
{
  "tool": "setup_replication",
  "args": {
    "actor_class": "/Game/Blueprints/Character_BP.Character_BP_C",
    "properties": ["Health", "Mana", "Location"],
    "replication_frequency": 10.0
  }
}
```
