# Project: Cerco da Fortaleza contra Isectum (Godot Engine 4)

## Strategic Scope & Architecture
- **Engine**: Godot Engine 4.x (Compatibility Renderer, 1280x720 base viewport, 2D mode, WebAssembly + Desktop exportable).
- **Core Game**: Tactical fortress defense and deckbuilding board game with co-op synchrony against the Isectum swarm.
- **Language**: Statically typed GDScript (`@export`, explicit types, class_name declarations, strict typing).
- **Architecture**: Decoupled clean architecture, single responsibility, data-driven (`Custom Resources`), event-driven communication via global `EventBus.gd`.
- **Autoload Singletons**:
  - `GameManager.gd`: Game state machine (`MENU`, `CERCO_FORTALEZA`, `FIM_DE_JOGO`, `MULTIPLAYER_LOBBY`).
  - `EventBus.gd`: Global event dispatcher (`zone_entered`, `card_played`, `dice_rolled`, `damage_dealt`, `production_completed`, `synergy_triggered`, `round_resolved`, `network_message_received`, `network_connection_status_changed`, `unit_moved`, `unit_attacked`, `unit_damaged`, `unit_died`, `status_applied`, `status_removed`).
  - `DataManager.gd`: Centralized loader for cards, castes, and fortress configurations.
  - `AudioManager.gd`: Global SFX and BGM manager with headless safety and zero leaks.
- **Testing Architecture**: GUT (Godot Unit Testing) in `godot_project/addons/gut/` and `godot_project/test/`, executed headless (`godot --headless -s addons/gut/gut_cmdln.gd -gexit`).

---

## 17 Logical Fortress Zones (20x20 Grid Mapping)
1. **Câmara Central** (Centro de comando / Vitória dos Isectum se conquistada)
2. **Carpintaria** (Oficina de processamento de Madeira)
3. **Curtume** (Oficina de processamento de Couro)
4. **Fundição** (Oficina de processamento de Metal e Cristal)
5. **Pátio Central** (Área de circulação e transição entre oficinas e muralhas)
6–9. **4 Muralhas** (Muralha Norte, Muralha Sul, Muralha Leste, Muralha Oeste - Barreira física e elevação +1)
10–13. **4 Torres de Vigia** (Torre NO, Torre NE, Torre SO, Torre SE - Disparos de balestra à distância e elevação +2)
14–17. **4 Campos de Invasão / Spawn** (Exterior Norte, Exterior Sul, Exterior Leste, Exterior Oeste)

---

## Feature Inventory & Milestones
| # | Feature | Description | Milestone | Status |
|---|---------|-------------|-----------|--------|
| 1 | Godot 4 Base Project & Autoloads | Viewport 1280x720, Compatibility, EventBus, DataManager, GameManager, AudioManager | M1 | Concluído (110 testes GUT, 0 leaks) |
| 2 | Tabuleiro da Fortaleza (17 Zonas) | Mapeamento das 17 zonas na grade 20x20, elevações, adjacências, bloqueios e fluxo de invasão | M2 | Concluído (237 testes GUT, 0 leaks) |
| 3 | Motor do Cerco (D6 Custom & Juiz) | Dados D6 (Impactos e Balestra), Melee (2 impactos = 1 dano), Balestra (1 disparo = 1 dano), Brutamontes, Infiltradores | M2 | Concluído (237 testes GUT, 0 leaks) |
| 4 | 24 Castas Isectum & Decks de Ameaça | 24 Castas originais de castas_isectum.py, habilidades únicas, cartas de Runa e Defesa | M3 | Concluído (276 testes GUT, 0 leaks) |
| 5 | Deckbuilder & Economia de Oficinas | Cartas de Ação (Marcha, Trabalho, Escavação), mercado de upgrades, produção (Madeira, Couro, Metal, Cristal) | M4 | Concluído (344 testes GUT, 0 leaks) |
| 6 | Turno de Sincronia Co-op & Sinergias | Sincronia simultânea, combos de Equipe (mesmo tipo) e Sinergia Suprema (todos iguais -> +2 cristais) | M4 | Concluído (379 testes GUT, 0 leaks) |
| 7 | HUD do Cerco, Tabuleiro & Áudio | Cartas em leque interativas, destaque visual de zonas, placar de recursos e log do cerco | M5 | Concluído (379 testes GUT, 0 leaks) |
| 8 | Cliente WebSocket Multiplayer Co-op | WebSocketPeer nativo, FSM 5 estados, 9 ações tipadas, auto-reconexão com backoff | M6 | Concluído (463 testes GUT, 0 leaks) |
| 9 | Cena de Entidades (Character.tscn/gd) | Node2D/CharacterBody2D, sprite mapping 54 assets, barra retro HP, status badges, highlight | Entidades | Concluído (510 testes GUT, 0 leaks) |
| 10 | Suíte GUT Final do Cerco & Hardening | 100% headless pass (510/510 testes, 5605 asserções), 0 ObjectDB leaks, Victory Audit Certified CLEAN | M7 | Concluído (100% Finalizado) |

---

## Final Project Verification (GUT Headless)
- Execução: `cd godot_project && ./run_gut_tests.sh`
- Suites Executadas: 17 suites
- Testes Rodados: 510 testes
- Testes Passados: 510 testes (100.0% de sucesso)
- Asserções Passadas: 5605 asserções (0 falhas)
- Leaks: Strictly 0 ObjectDB memory leaks na saída verbose
- Certificação: Forensic Victory Audit CLEAN (100% Complete)
