# Blueprint Forge

Плагин для создания и управления Actor Blueprint через Python API Unreal Engine 5.7.

## Возможности

- Создание Actor Blueprint с заданными компонентами
- Клонирование существующих Blueprint
- Добавление/удаление компонентов в существующие Blueprint
- Получение списка компонентов Blueprint
- Компиляция Blueprint и проверка ошибок
- Управление переменными Blueprint (чтение/запись)
- Автоматическая настройка свойств компонентов

## Инструменты

### create_blueprint

Создаёт новый Actor Blueprint с указанными компонентами.

**Параметры:**
- `blueprint_name` (string): Имя создаваемого Blueprint
- `components` (array): Список компонентов для добавления
  - `type`: Тип компонента (static_mesh, box_collision, sphere_collision, capsule_collision, directional_light, point_light, spot_light, camera, audio, particle_system)
  - `name`: Имя компонента
  - `properties`: Свойства компонента (опционально)
- `parent_class` (string, опционально): Родительский класс (по умолчанию "Actor")

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
- `components_added` (array): Список добавленных компонентов
- `message` (string): Сообщение о результате

---

### duplicate_blueprint

Создаёт копию существующего Blueprint с новым именем.

**Параметры:**
- `source_blueprint` (string): Путь к исходному Blueprint (например, /Game/Blueprints/OldBP)
- `new_name` (string): Имя для нового Blueprint
- `destination_path` (string, опционально): Путь назначения (по умолчанию /Game/Blueprints)

**Пример использования:**
```json
{
    "source_blueprint": "/Game/Blueprints/OldBP",
    "new_name": "NewBP",
    "destination_path": "/Game/Blueprints"
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `new_path` (string): Путь к новому Blueprint
- `message` (string): Сообщение о результате

---

### add_component_to_blueprint

Добавляет новый компонент в существующий Blueprint.

**Параметры:**
- `blueprint_path` (string): Путь к Blueprint (например, /Game/Blueprints/MyBP)
- `component_type` (string): Тип добавляемого компонента
- `component_name` (string): Имя компонента
- `properties` (object, опционально): Свойства компонента

**Пример использования:**
```json
{
    "blueprint_path": "/Game/Blueprints/MyBP",
    "component_type": "point_light",
    "component_name": "Light",
    "properties": {"intensity": 1000}
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `component_name` (string): Имя добавленного компонента
- `component_type` (string): Тип компонента
- `message` (string): Сообщение о результате

---

### remove_component_from_blueprint

Удаляет указанный компонент из Blueprint. **Требует подтверждения (destructive).**

**Параметры:**
- `blueprint_path` (string): Путь к Blueprint
- `component_name` (string): Имя удаляемого компонента

**Пример использования:**
```json
{
    "blueprint_path": "/Game/Blueprints/MyBP",
    "component_name": "Light"
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `component_name` (string): Имя удалённого компонента
- `message` (string): Сообщение о результате

---

### list_blueprint_components

Возвращает список всех компонентов указанного Blueprint.

**Параметры:**
- `blueprint_path` (string): Путь к Blueprint

**Пример использования:**
```json
{
    "blueprint_path": "/Game/Blueprints/MyBP"
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `blueprint_path` (string): Путь к Blueprint
- `components` (array): Список компонентов с информацией (name, class, is_inherited)
- `total_count` (int): Общее количество компонентов
- `message` (string): Сообщение о результате

---

### compile_blueprint

Компилирует указанный Blueprint и проверяет наличие ошибок.

**Параметры:**
- `blueprint_path` (string): Путь к Blueprint

**Пример использования:**
```json
{
    "blueprint_path": "/Game/Blueprints/MyBP"
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность компиляции
- `blueprint_path` (string): Путь к Blueprint
- `message` (string): Сообщение о результате

---

### get_blueprint_variables

Возвращает список всех переменных (member variables) Blueprint.

**Параметры:**
- `blueprint_path` (string): Путь к Blueprint

**Пример использования:**
```json
{
    "blueprint_path": "/Game/Blueprints/MyBP"
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `blueprint_path` (string): Путь к Blueprint
- `variables` (array): Список переменных (name, type, is_public)
- `total_count` (int): Общее количество переменных
- `message` (string): Сообщение о результате

---

### set_blueprint_variable

Устанавливает значение указанной переменной Blueprint. **Требует подтверждения (destructive).**

**Параметры:**
- `blueprint_path` (string): Путь к Blueprint
- `variable_name` (string): Имя переменной
- `value` (string|number|boolean|object): Значение переменной

**Пример использования:**
```json
{
    "blueprint_path": "/Game/Blueprints/MyBP",
    "variable_name": "Health",
    "value": 100
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `blueprint_path` (string): Путь к Blueprint
- `variable_name` (string): Имя переменной
- `value` (any): Установленное значение
- `message` (string): Сообщение о результате
