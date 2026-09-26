# res://addons/gut/gut_cmdln.gd
extends SceneTree

## Headless CLI Test Runner for GUT (Godot Unit Test) in Godot 4.
## Discovers and runs tests headlessly, reporting results with exit code 0 or 1.

var _exit_on_finish: bool = false
var _target_dir: String = "res://test/unit/"
var _target_test: String = ""
var _target_method: String = ""
var _prefix: String = "test_"
var _suffix: String = ".gd"

var _total_tests_run: int = 0
var _total_tests_passed: int = 0
var _total_tests_failed: int = 0
var _total_assertions: int = 0
var _total_passed_assertions: int = 0
var _total_failed_assertions: int = 0

func _init() -> void:
	_parse_arguments()
	_load_config_file()
	_run_tests.call_deferred()

func _parse_arguments() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		args = OS.get_cmdline_args()

	for arg in args:
		if arg == "-gexit" or arg == "--gexit":
			_exit_on_finish = true
		elif arg.begins_with("-gdir="):
			_target_dir = arg.split("=")[1]
		elif arg.begins_with("-gtest="):
			_target_test = arg.split("=")[1]
		elif arg.begins_with("-gunit_test_name="):
			_target_method = arg.split("=")[1]
		elif arg.begins_with("-gprefix="):
			_prefix = arg.split("=")[1]
		elif arg.begins_with("-gsuffix="):
			_suffix = arg.split("=")[1]

func _load_config_file() -> void:
	var config_path: String = "res://.gutconfig.json"
	if FileAccess.file_exists(config_path):
		var file: FileAccess = FileAccess.open(config_path, FileAccess.READ)
		if file != null:
			var json_text: String = file.get_as_text()
			file.close()
			var json: JSON = JSON.new()
			if json.parse(json_text) == OK and json.data is Dictionary:
				var dict: Dictionary = json.data
				if dict.get("exit_on_finish", false) or dict.get("should_exit", false):
					_exit_on_finish = true
				if dict.has("dirs") and dict["dirs"] is Array and not dict["dirs"].is_empty():
					_target_dir = dict["dirs"][0]
				if dict.has("prefix"):
					_prefix = dict["prefix"]
				if dict.has("suffix"):
					_suffix = dict["suffix"]

func _initialize_autoloads() -> void:
	var cf: ConfigFile = ConfigFile.new()
	if cf.load("res://project.godot") == OK:
		if cf.has_section("autoload"):
			for key in cf.get_section_keys("autoload"):
				var path_str: String = cf.get_value("autoload", key)
				if path_str.begins_with("*"):
					path_str = path_str.substr(1)
				if not root.has_node(key):
					if FileAccess.file_exists(path_str):
						var script = load(path_str)
						if script != null:
							var instance = script.new()
							instance.name = key
							root.add_child(instance)

func _run_tests() -> void:
	_initialize_autoloads()

	print("\n============================================================")
	print("                    GUT TEST RUNNER                         ")
	print("============================================================")
	print("Scanning directory: ", _target_dir)

	var test_files: Array[String] = []
	if not _target_test.is_empty():
		test_files.append(_target_test)
	else:
		_find_test_files(_target_dir, test_files)

	print("Found %d test script(s)." % test_files.size())

	for file_path in test_files:
		_run_test_file(file_path)

	print("\n============================================================")
	print("                    TEST SUMMARY                            ")
	print("============================================================")
	print("Test Scripts Executed:   %d" % test_files.size())
	print("Tests Run:               %d" % _total_tests_run)
	print("Tests Passed:            %d" % _total_tests_passed)
	print("Tests Failed:            %d" % _total_tests_failed)
	print("Total Assertions:        %d" % _total_assertions)
	print("Assertions Passed:       %d" % _total_passed_assertions)
	print("Assertions Failed:       %d" % _total_failed_assertions)
	print("============================================================\n")

	var exit_code: int = 0 if (_total_failed_assertions == 0 and _total_tests_failed == 0) else 1

	if _exit_on_finish:
		quit(exit_code)

func _find_test_files(dir_path: String, results: Array[String]) -> void:
	var dir: DirAccess = DirAccess.open(dir_path)
	if dir == null:
		return

	dir.list_dir_begin()
	var file_name: String = dir.get_next()
	while not file_name.is_empty():
		if dir.current_is_dir() and not file_name.begins_with("."):
			_find_test_files(dir_path.path_join(file_name), results)
		elif file_name.begins_with(_prefix) and file_name.ends_with(_suffix):
			results.append(dir_path.path_join(file_name))
		file_name = dir.get_next()
	dir.list_dir_end()

func _run_test_file(file_path: String) -> void:
	print("\n--- Running Suite: %s ---" % file_path)
	var script = load(file_path)
	if script == null:
		push_error("Failed to load test script: %s" % file_path)
		_total_tests_failed += 1
		return

	var test_instance = script.new()
	if not (test_instance is GutTest):
		push_error("Test script does not inherit from GutTest: %s" % file_path)
		_total_tests_failed += 1
		return

	root.add_child(test_instance)

	# Discover test methods
	var methods: Array[String] = []
	for method_info in test_instance.get_method_list():
		var m_name: String = method_info["name"]
		if m_name.begins_with("test_"):
			if _target_method.is_empty() or m_name == _target_method:
				methods.append(m_name)

	# Lifecycle: before_all
	if test_instance.has_method("before_all"):
		test_instance.before_all()

	# Execute each test
	for m_name in methods:
		_total_tests_run += 1
		var starting_fails: int = test_instance._failed_count

		test_instance._internal_before_each(m_name)
		if test_instance.has_method("before_each"):
			test_instance.before_each()

		test_instance.call(m_name)

		if test_instance.has_method("after_each"):
			test_instance.after_each()
		test_instance._internal_after_each()

		var test_failed: bool = (test_instance._failed_count > starting_fails)
		if test_failed:
			_total_tests_failed += 1
			print("  [FAIL] %s" % m_name)
			for fail_msg in test_instance._failure_messages:
				print("    -> %s" % fail_msg)
			test_instance._failure_messages.clear()
		else:
			_total_tests_passed += 1
			print("  [PASS] %s" % m_name)

	# Lifecycle: after_all
	if test_instance.has_method("after_all"):
		test_instance.after_all()

	_total_assertions += test_instance._assertion_count
	_total_passed_assertions += test_instance._passed_count
	_total_failed_assertions += test_instance._failed_count

	root.remove_child(test_instance)
	test_instance.queue_free()
