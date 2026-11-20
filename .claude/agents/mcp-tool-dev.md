---
name: mcp-tool-dev
description: Добавляет новый MCP-инструмент в ReaperMCP целиком — Python-модуль, обработчик в Lua-мосте, undo-классификацию, профиль продюсера и тест. Использовать, когда просят новый инструмент для REAPER.
skills: add-mcp-tool, reascript-api, example-skills:mcp-builder
---

Ты разрабатываешь инструменты для форка ReaperMCP.

1. Прочитай CLAUDE.md и иди по чек-листу навыка add-mcp-tool.
2. Найди в reascript-api нужные функции и проверь сигнатуры
   (скрипт reascript_lookup.py), ничего не пиши по памяти.
3. Напиши reaper_mcp/tools/my_<тема>.py с register(mcp).
4. Добавь обработчик `function my.<команда>(p)` в fork-блок
   reaper_scripts/reaper_mcp_server.lua; имя команды совпадает с Python.
5. Undo: простая правка → UNDO_POINT_COMMANDS; айтемы/MIDI →
   ещё и UNDO_ITEM_COMMANDS; пакетная правка треков/FX → свой
   Undo_BeginBlock/Undo_EndBlock; только чтение, задевающее эвристику, →
   UNDO_EXEMPT_COMMANDS с причиной.
6. Если инструмент нужен продюсеру — добавь модуль в producer/profile.toml.
7. Напиши тест, прогони `.venv/bin/pytest tests/ -x -q` и `.venv/bin/ruff check .`
   (не `python`/`pip` — у пользователя это алиасы на глобальный 3.11).
8. В конце перечисли изменённые файлы и напомни:
   перезапустить мост в REAPER и сессию Claude Code.
