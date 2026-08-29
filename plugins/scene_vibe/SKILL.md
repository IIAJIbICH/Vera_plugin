# Scene Vibe

Плагин для применения настроения сцены через DirectionalLight и PostProcessVolume в Unreal Engine 5.7.

## Возможности

- Применение预设 настроений (mood presets)
- Настройка освещения через DirectionalLight
- Настройка пост-обработки через PostProcessVolume
- Очистка всех помеченных акторов

## Инструменты

### set_vibe

Применяет настроение сцены через настройку освещения и пост-обработки.

**Параметры:**
- `mood` (string): Тип настроения (day, night, sunset, horror, sci-fi, warm, cold)
- `intensity` (float): Интенсивность эффекта (0.0-1.0, по умолчанию 1.0)
- `apply_to_volume` (bool): Применить к существующему PostProcessVolume (по умолчанию true)

**Пример использования:**
```json
{
    "mood": "sunset",
    "intensity": 0.8
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `actors_modified` (int): Количество изменённых акторов
- `message` (string): Сообщение о результате

### clear_vibe

Удаляет все помеченные акторы, созданные плагином Scene Vibe.

**Параметры:**
- `confirm` (bool): Подтверждение удаления (обязательно true)

**Пример использования:**
```json
{
    "confirm": true
}
```

**Возвращаемое значение:**
- `success` (bool): Успешность операции
- `actors_deleted` (int): Количество удалённых акторов
- `message` (string): Сообщение о результате
