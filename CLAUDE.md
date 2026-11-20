# ReaperMCP (форк)

Форк `xDarkzx/Reaper-MCP`: `origin` — форк, `upstream` — оригинал.

## Архитектура
Python (FastMCP) пишет command.json → Lua-скрипт в REAPER читает,
выполняет через ReaScript API и пишет response.json.
Обменный каталог — `$TMPDIR/reaper_mcp` (общий для всех сессий).
Подробно: docs/ARCHITECTURE.md, правила upstream: CONTRIBUTING.md.

## Как добавить инструмент
1. Модуль `reaper_mcp/tools/my_<тема>.py` с функцией `register(mcp)`.
   Реестр (`reaper_mcp/tool_registry.py`) импортирует его сам, но имя модуля
   нужно добавить в `_EXPECTED_MODULES` того же файла строкой
   `"my_<тема>",  # fork:` — иначе падает tests/test_tool_registry.py. Внутри: `@mcp.tool()`, валидация входа (диапазоны чисел,
   длина строк), вызов `await client.execute("<команда>", **params)`
   (`execute_long` — для долгих пакетных записей). Образец —
   `reaper_mcp/tools/transport_tools.py`.
2. Обработчик в `reaper_scripts/reaper_mcp_server.lua`
   (диспетчер статический: без обработчика команда вернёт
   «Unknown command»). Свои обработчики — в таблице `my`
   (`function my.<команда>(p)`) в блоке `-- fork:` перед разделом
   «Command dispatch table»; таблица подключается строкой
   `for k, v in pairs(my) do handlers[k] = v end -- fork:` сразу после
   `pairs(script)` (уже есть). Имена `my.*` не должны совпадать с upstream:
   при совпадении обработчик молча перекрывается.
   Имя команды в Python == имя функции в Lua. Возврат: таблица с данными
   или `nil, "текст ошибки"`. Треки — через `get_track(p, key)` /
   `get_numbered_track(p, key)` (индекс -1 = мастер).
   Никаких `load` / `dofile` / `loadstring`.
3. Undo — решение обязательно для каждого мутирующего обработчика
   (иначе падает tests/test_lua_undo_points.py):
   - простая правка (фейдер, FX, маркер, send…) → добавить в `UNDO_POINT_COMMANDS`;
   - правка айтемов/MIDI/тейков → в `UNDO_POINT_COMMANDS` и `UNDO_ITEM_COMMANDS`
     (Undo-блоки REAPER не сохраняют MIDI);
   - пакетная правка треков/FX/роутинга → свой `reaper.Undo_BeginBlock()` /
     `reaper.Undo_EndBlock(...)` внутри обработчика;
   - только чтение, но вызывает Set*/Get*Set* и т.п. → `UNDO_EXEMPT_COMMANDS`
     с причиной.
4. Профили (`BUILTIN_PROFILES` в tool_registry.py — списки модулей):
   `full` включает все модули автоматически. Продюсер работает через
   `producer/profile.toml` (`REAPER_MCP_PROFILE_FILE`): чтобы инструмент
   был у продюсера, добавь модуль в `include_modules` этого файла.
   `BUILTIN_PROFILES` upstream не правим.
5. Тест в `tests/test_my_<тема>.py` (Python-часть мокает ReaperClient;
   Lua-часть можно гонять через `lupa`, см. tests/test_lua_master_guard.py).
6. Прогнать тесты и линтер (ниже).

## Команды
В zsh пользователя `python`/`pip` — алиасы на 3.11 и перекрывают venv.
Всегда вызывай бинарники venv явно:
- Тесты: `.venv/bin/pytest tests/ -x -q`
- Линтер: `.venv/bin/ruff check .`
- Установка: `.venv/bin/python -m pip install -e ".[dev,analysis]"`
- Состав встроенного профиля: `.venv/bin/reaper-mcp --profile-info <профиль>`
- Состав профиля продюсера (имя не указывать — иначе покажет `full`):
  `REAPER_MCP_PROFILE_FILE=producer/profile.toml .venv/bin/reaper-mcp --profile-info`

## Правила
- Перед началом работы перечитай этот файл и .claude/.
- Свой код — только в файлах `my_*`; файлы upstream меняй
  минимально и помечай комментарием `-- fork:` / `# fork:`.
- `reaper_mcp/mix_engine/` не трогать без прямой просьбы.
- После изменения Lua напомни перезапустить мост в REAPER,
  после нового инструмента — перезапустить сессию Claude Code.
- Не запускать одновременно сессии разработчика и продюсера.
- Отвечай по-русски.
