# Blueprint Forge

Плагин для создания Actor Blueprint с компонентами через Python API Unreal Engine 5.7.

## Возможности

- Создание Actor Blueprint с заданными компонентами
- Добавление Static Mesh, Box Collision и других компонентов
- Автоматическая настройка свойств компонентов

## Инструменты

### create_blueprint

Создаёт новый Actor Blueprint с указанными компонентами.

**Параметры:**
- `blueprint_name` (string): Имя создаваемого Blueprint
- `components` (array): Список компонентов для добавления
  - `type`: Тип компонента (static_mesh, box_collision, sphere_collision, directional_light, point_light, camera)
  - `name`: Имя компонента
  - `properties`: Свойства компонента (опционально)

**Пример использования:**
```json
{
    "blueprint_name": "MyActor",
    "components": [
        {"type": "static_mesh", "name": "Mesh"},
        {"type": "box_collision", "name": "Collision"}
    ]
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `blueprint_path` (string): Путь к созданному Blueprint
- `message` (string): Сообщение о результате
