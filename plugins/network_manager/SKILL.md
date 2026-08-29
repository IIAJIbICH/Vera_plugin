# Network Manager Plugin

Инструменты для настройки сетевой инфраструктуры MMO в Unreal Engine 5.7.

## Инструменты

### 1. setup_replication
Настройка репликации для Actor Blueprint или C++ класса.

**Параметры:**
- `asset_path` (required): Путь к Blueprint или классу
- `replicated_variables`: Список переменных для репликации
- `replication_frequency`: High, Medium, Low

**destructive = True**

### 2. configure_rpc
Настройка Remote Procedure Calls (Server, Client, Multicast).

**Параметры:**
- `asset_path` (required): Путь к Blueprint или классу
- `rpc_type` (required): Server, Client, Multicast, NetMulticast
- `function_name` (required): Имя функции
- `is_reliable`: Надёжная доставка

**destructive = True**

### 3. test_network_profiling
Тестирование сетевой производительности.

**Параметры:**
- `test_duration`: Длительность теста (сек)
- `simulate_latency`: Имитация задержки (мс)
- `simulate_packet_loss`: Потеря пакетов (0.0-1.0)

### 4. create_dedicated_server_config
Создание конфигурации для выделенного сервера.

**Параметры:**
- `server_name` (required): Имя сервера
- `max_players`: Максимум игроков
- `maps`: Список карт
- `port`: Порт сервера

### 5. setup_session_system
Настройка системы игровых сессий.

**Параметры:**
- `session_name`: Имя сессии
- `max_players`: Максимум игроков
- `use_lan`: LAN режим
- `presence_enabled`: Статус игрока

## Примеры

```python
await vera.call("setup_replication", {
    "asset_path": "/Game/Blueprints/BP_Player",
    "replicated_variables": ["Health", "Mana", "Position"],
    "replication_frequency": "High"
})

await vera.call("configure_rpc", {
    "asset_path": "/Game/Blueprints/BP_Player",
    "rpc_type": "Server",
    "function_name": "ServerAttack",
    "is_reliable": True
})

await vera.call("create_dedicated_server_config", {
    "server_name": "MyMMO_Server",
    "max_players": 100,
    "maps": ["/Game/Maps/MainWorld"],
    "port": 7777
})
```
