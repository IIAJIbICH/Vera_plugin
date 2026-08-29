# PCG Forge

Плагин для создания и настройки PCG (Procedural Content Generation) графов в Unreal Engine 5.7.

## Инструменты

### build_pcg_graph

Добавляет ноды в PCG граф для процедурной генерации.

**Параметры:**
- `graph_name` (string): Имя PCG графа (обязательно)
- `nodes` (array): Список нод для добавления
  - `type`: Тип ноды (LandscapeData, SurfaceSampler, Spawner, Transform, Filter)
  - `name`: Имя ноды
  - `settings`: Настройки ноды

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `graph_path` (string): Путь к графу
- `nodes_added` (int): Количество добавленных нод
