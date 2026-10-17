# res://test/unit/test_meta_progression.gd
extends GutTest

## Testes Unitários: Meta-Progressão Permanente & Ascensão (Marcos M7 & M8)
## Valida persistência de Âmbar Real, desbloqueio de heróis no Quartel,
## Bestiário e modificadores dos 10 Níveis de Ascensão.

const TEST_SAVE_PATH: String = "user://test_meta_save.json"

var _meta: MetaProgression

func before_each() -> void:
	# Garante que arquivo de teste anterior não interfira
	if FileAccess.file_exists(TEST_SAVE_PATH):
		DirAccess.remove_absolute(TEST_SAVE_PATH)
	_meta = MetaProgression.new(TEST_SAVE_PATH)

func after_each() -> void:
	if _meta != null:
		_meta = null
	if FileAccess.file_exists(TEST_SAVE_PATH):
		DirAccess.remove_absolute(TEST_SAVE_PATH)

# ── 1. Inicialização & Valores Padrão ─────────────────────────────────────────

func test_default_initialization() -> void:
	# Assert
	assert_eq(_meta.amber_balance, 0)
	assert_eq(_meta.lifetime_amber, 0)
	assert_eq(_meta.current_ascension, 0)
	assert_eq(_meta.max_unlocked_ascension, 0)
	assert_false(_meta.is_hero_unlocked("aquele"), "Aquele is secret and must not be unlocked by default")
	assert_true(_meta.is_hero_unlocked("stark"))
	assert_true(_meta.is_hero_unlocked("elden"))
	assert_true(_meta.is_hero_unlocked("novak"))
	assert_false(_meta.is_hero_unlocked("doom"))
	assert_false(_meta.is_hero_unlocked("koema"))

# ── 2. Economia de Âmbar Real ─────────────────────────────────────────────────

func test_deposit_and_spend_amber_happy_path() -> void:
	# Arrange
	watch_signals(_meta)

	# Act 1: Depósito
	var ok_dep: bool = _meta.deposit_amber(100)

	# Assert 1
	assert_true(ok_dep)
	assert_eq(_meta.amber_balance, 100)
	assert_eq(_meta.lifetime_amber, 100)
	assert_signal_emitted_with_parameters(_meta, "amber_changed", [100, 100])

	# Act 2: Gasto
	var ok_spend: bool = _meta.spend_amber(40)

	# Assert 2
	assert_true(ok_spend)
	assert_eq(_meta.amber_balance, 60)
	assert_eq(_meta.lifetime_amber, 100, "Lifetime amber não diminui com gastos")
	assert_signal_emitted_with_parameters(_meta, "amber_changed", [60, -40])

func test_amber_economy_edge_cases() -> void:
	# Arrange
	_meta.deposit_amber(50)

	# Act & Assert
	assert_false(_meta.deposit_amber(0), "Depósito zero deve falhar")
	assert_false(_meta.deposit_amber(-20), "Depósito negativo deve falhar")
	assert_false(_meta.spend_amber(0), "Gasto zero deve falhar")
	assert_false(_meta.spend_amber(-10), "Gasto negativo deve falhar")
	assert_false(_meta.spend_amber(60), "Gastar mais que o saldo deve falhar")
	assert_eq(_meta.amber_balance, 50, "Saldo deve permanecer intacto")

# ── 3. Quartel dos Heróis ─────────────────────────────────────────────────────

func test_unlock_hero_with_sufficient_amber() -> void:
	# Arrange: Doom custa 30 de Âmbar
	_meta.deposit_amber(50)
	watch_signals(_meta)

	# Act
	var can_unlock: bool = _meta.can_unlock_hero("doom")
	var unlocked: bool = _meta.unlock_hero("doom")

	# Assert
	assert_true(can_unlock)
	assert_true(unlocked)
	assert_true(_meta.is_hero_unlocked("doom"))
	assert_eq(_meta.amber_balance, 20, "50 - 30 = 20 de Âmbar restante")
	assert_signal_emitted_with_parameters(_meta, "hero_unlocked", ["doom"])

func test_cannot_unlock_hero_with_insufficient_amber() -> void:
	# Arrange: Koema custa 150 de Âmbar; jogador possui apenas 100
	_meta.deposit_amber(100)

	# Act
	var can_unlock: bool = _meta.can_unlock_hero("koema")
	var unlocked: bool = _meta.unlock_hero("koema")

	# Assert
	assert_false(can_unlock)
	assert_false(unlocked)
	assert_false(_meta.is_hero_unlocked("koema"))
	assert_eq(_meta.amber_balance, 100)

func test_cannot_unlock_already_unlocked_or_invalid_hero() -> void:
	# Arrange
	_meta.deposit_amber(200)

	# Act & Assert
	assert_false(_meta.can_unlock_hero("stark"), "Herói inicial já está desbloqueado")
	assert_false(_meta.unlock_hero("stark"))
	assert_false(_meta.can_unlock_hero("aquele"), "Herói secreto não pode ser comprado por Âmbar regular")
	assert_false(_meta.unlock_hero("aquele"))
	assert_false(_meta.can_unlock_hero("heroi_inexistente"), "Herói desconhecido")
	assert_false(_meta.unlock_hero("heroi_inexistente"))

# ── 4. Códice & Bestiário Isectum ──────────────────────────────────────────────

func test_record_caste_encounter_and_prevent_duplicates() -> void:
	# Arrange
	watch_signals(_meta)

	# Act 1
	var first_rec: bool = _meta.record_caste_encounter("viuva_canibal")

	# Assert 1
	assert_true(first_rec)
	assert_true(_meta.is_caste_in_codex("viuva_canibal"))
	assert_signal_emitted_with_parameters(_meta, "caste_recorded", ["viuva_canibal"])

	# Act 2 (Duplicata)
	var dup_rec: bool = _meta.record_caste_encounter("viuva_canibal")

	# Assert 2
	assert_false(dup_rec)
	assert_eq(_meta.codex_castes.size(), 1)

# ── 5. Sistema de Ascensão (1 a 10) ───────────────────────────────────────────

func test_ascension_locked_before_victory() -> void:
	# Act & Assert
	assert_false(_meta.is_ascension_unlocked())
	assert_false(_meta.set_ascension_level(1), "Não pode subir de ascensão sem vencer o jogo antes")
	assert_eq(_meta.current_ascension, 0)

func test_ascension_unlocked_after_victory_and_modifiers() -> void:
	# Arrange: Simula uma run vitoriosa
	var run: RunState = RunState.new()
	run.status = RunState.Status.VICTORY
	run.floors_cleared = 12
	run.bosses_defeated = 3
	watch_signals(_meta)

	# Act
	var summary: Dictionary = _meta.record_run_finished(run, true)

	# Assert
	assert_true(summary.victory)
	assert_true(_meta.is_ascension_unlocked())
	assert_eq(_meta.max_unlocked_ascension, 1)

	# Pode selecionar Ascensão 1
	assert_true(_meta.set_ascension_level(1))
	assert_eq(_meta.current_ascension, 1)

	var mods: Dictionary = _meta.get_ascension_modifiers(1)
	assert_eq(mods.enemy_hp_multiplier, 1.10, "Ascensão 1 concede +10% de PV aos inimigos")

	var mods_10: Dictionary = _meta.get_ascension_modifiers(10)
	assert_eq(mods_10.rei_frenzy_threshold, 200, "Ascensão 10 antecipa o Frenesi do Rei para 200 PV")

# ── 6. Persistência em Disco & Recuperação de Erros ───────────────────────────

func test_save_and_load_roundtrip() -> void:
	# Arrange
	_meta.deposit_amber(250)
	_meta.unlock_hero("gruu")
	_meta.record_caste_encounter("cigarra_ressonante")
	_meta.total_victories = 2
	_meta.max_unlocked_ascension = 2
	_meta.current_ascension = 1

	# Act
	var saved_ok: bool = _meta.save_to_disk()
	assert_true(saved_ok)
	assert_true(FileAccess.file_exists(TEST_SAVE_PATH))

	var new_meta: MetaProgression = MetaProgression.new(TEST_SAVE_PATH)
	var loaded_ok: bool = new_meta.load_from_disk()

	# Assert
	assert_true(loaded_ok)
	assert_eq(new_meta.amber_balance, 250 - 40, "250 depositados - 40 de Gruu = 210")
	assert_true(new_meta.is_hero_unlocked("gruu"))
	assert_true(new_meta.is_caste_in_codex("cigarra_ressonante"))
	assert_eq(new_meta.total_victories, 2)
	assert_eq(new_meta.max_unlocked_ascension, 2)
	assert_eq(new_meta.current_ascension, 1)

func test_load_corrupted_file_handles_gracefully() -> void:
	# Arrange: Grava lixo sintético no arquivo
	var f: FileAccess = FileAccess.open(TEST_SAVE_PATH, FileAccess.WRITE)
	f.store_string("{{ESTE_NAO_E_UM_JSON_VALIDO}}")
	f.close()

	# Act
	var ok: bool = _meta.load_from_disk()

	# Assert
	assert_false(ok, "Arquivo corrompido deve retornar false de forma segura sem crash")
	assert_eq(_meta.amber_balance, 0)
