# res://test/unit/test_secret_hero_rules.gd
extends GutTest

## Test Suite: Regras de Personagem Secreto (Aquele)
## Valida que Aquele foi removido da seleção pública e do grupo inicial,
## atuando estritamente como personagem secreto desbloqueável por condições especiais.

const TEST_SAVE_PATH: String = "user://test_secret_hero_save.json"

var _timer: SceneTreeTimer = null
var _meta: MetaProgression = null

func before_all() -> void:
	# Watchdog timer de 10s (RULE[prevencao_execucao_infinita])
	_timer = get_tree().create_timer(10.0)

func before_each() -> void:
	if FileAccess.file_exists(TEST_SAVE_PATH):
		DirAccess.remove_absolute(TEST_SAVE_PATH)
	_meta = MetaProgression.new(TEST_SAVE_PATH)

func after_each() -> void:
	_meta = null
	if FileAccess.file_exists(TEST_SAVE_PATH):
		DirAccess.remove_absolute(TEST_SAVE_PATH)

func test_aquele_is_removed_from_public_cerco_setup_hero_selection() -> void:
	# Arrange & Act
	var setup: CercoSetup = autofree(CercoSetup.new())
	setup._ready()

	# Assert
	assert_false(setup.selected_heroes.has("Aquele"), "Aquele must NOT be present in public selection dictionary")
	for h_def in CercoSetup.HERO_DEFS:
		assert_ne(str(h_def.get("id")), "Aquele", "Aquele must not be in public HERO_DEFS")
	assert_true(setup.selected_heroes.has("Stark"), "Stark must be the public default leader")
	assert_true(setup.selected_heroes["Stark"], "Stark must start selected by default")

func test_default_run_party_does_not_contain_aquele() -> void:
	# Arrange & Act
	var default_party: Dictionary = RunSession.DEFAULT_PARTY

	# Assert
	assert_false(default_party.has("aquele"), "Default roguelike party must not contain secret hero 'aquele'")
	assert_true(default_party.has("stark"), "Default party must contain Stark")
	assert_true(default_party.has("elden"), "Default party must contain Elden")
	assert_true(default_party.has("novak"), "Default party must contain Novak")
	assert_eq(default_party.size(), 3, "Party size must remain exactly 3 heroes")

func test_meta_progression_marks_aquele_as_secret_and_locks_by_default() -> void:
	# Arrange & Act
	var is_unlocked: bool = _meta.is_hero_unlocked("aquele")
	var is_secret: bool = _meta.is_hero_secret("aquele")

	# Assert
	assert_false(is_unlocked, "Secret hero 'aquele' must NOT be unlocked by default")
	assert_true(is_secret, "'aquele' must be classified as a secret hero")
	assert_false(_meta.can_unlock_hero("aquele"), "Secret hero cannot be purchased in standard amber shop")

func test_meta_progression_cannot_buy_aquele_via_standard_shop_even_with_infinite_amber() -> void:
	# Arrange
	_meta.deposit_amber(99999)

	# Act
	var can_buy: bool = _meta.can_unlock_hero("aquele")
	var bought: bool = _meta.unlock_hero("aquele")

	# Assert
	assert_false(can_buy, "Standard amber shop must not offer secret hero")
	assert_false(bought, "unlock_hero must fail for secret hero")
	assert_false(_meta.is_hero_unlocked("aquele"), "Aquele must remain locked")

func test_unlock_secret_hero_api_grants_access_and_persists() -> void:
	# Arrange
	watch_signals(_meta)
	assert_false(_meta.is_hero_unlocked("aquele"))

	# Act 1: Desbloqueio secreto bem-sucedido
	var ok_secret: bool = _meta.unlock_secret_hero("aquele")

	# Assert 1
	assert_true(ok_secret, "unlock_secret_hero must succeed for secret hero")
	assert_true(_meta.is_hero_unlocked("aquele"), "Aquele is now unlocked")
	assert_signal_emitted_with_parameters(_meta, "hero_unlocked", ["aquele"])

	# Act 2: Segundo desbloqueio idempotente deve falhar
	var ok_repeat: bool = _meta.unlock_secret_hero("aquele")
	assert_false(ok_repeat, "Duplicate unlock of secret hero must return false")

	# Act 3: Tentativa de desbloquear herói não secreto via API de segredo
	var ok_invalid: bool = _meta.unlock_secret_hero("stark")
	assert_false(ok_invalid, "unlock_secret_hero on non-secret hero must return false")
