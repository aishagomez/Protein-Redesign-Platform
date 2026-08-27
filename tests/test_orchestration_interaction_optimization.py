import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace


def _load_orchestration_module():
    module_path = Path(__file__).resolve().parents[1] / "api" / "services" / "orchestration.py"

    celery_module = ModuleType("celery_app")
    celery_module.celery_app = SimpleNamespace()
    sys.modules["celery_app"] = celery_module

    models_module = ModuleType("models")
    for name in ["Pipeline", "Project", "StageExecution", "Notification", "Tool"]:
        setattr(models_module, name, type(name, (), {}))
    sys.modules["models"] = models_module

    auth_module = ModuleType("services.auth")
    auth_module.is_admin_user_id = lambda *_args, **_kwargs: False
    sys.modules["services.auth"] = auth_module

    access_module = ModuleType("services.access")
    access_module.get_pipeline_by_id_for_user = lambda *_args, **_kwargs: None
    access_module.get_pipeline_for_user = lambda *_args, **_kwargs: None
    sys.modules["services.access"] = access_module

    file_storage_module = ModuleType("services.file_storage")
    file_storage_module.GENERATED_ROOT = Path(tempfile.gettempdir())
    sys.modules["services.file_storage"] = file_storage_module

    tasks_module = ModuleType("tasks")
    tasks_module.run_stage = SimpleNamespace(apply_async=lambda **kwargs: None)
    sys.modules["tasks"] = tasks_module

    services_package = ModuleType("services")
    services_package.__path__ = []
    sys.modules["services"] = services_package

    spec = importlib.util.spec_from_file_location("services.orchestration", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["services.orchestration"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InteractionOptimizationHydrationTests(unittest.TestCase):
    def test_uses_previous_stage_pdb_when_scenario_package_has_no_pdb(self):
        orchestration = _load_orchestration_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            scenario_dir = tmp_path / "scenario"
            scenario_dir.mkdir(parents=True, exist_ok=True)
            (scenario_dir / "faceA.txt").write_text("faceA", encoding="utf-8")
            (scenario_dir / "faceC.txt").write_text("faceC", encoding="utf-8")
            (scenario_dir / "msa_alignment.txt").write_text("msa", encoding="utf-8")

            pdb_path = tmp_path / "model.pdb"
            pdb_path.write_text("ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\n", encoding="utf-8")

            previous_stage = SimpleNamespace(stage_name="refinement", output_files=[str(pdb_path)])

            resolved = orchestration._hydrate_interaction_optimization_params(
                SimpleNamespace(),
                {
                    "scenario_path": str(scenario_dir),
                    "partners": "A_B",
                    "ligand_chain": "B",
                },
                [previous_stage],
            )

            self.assertEqual(resolved["complex_pdb_path"], str(pdb_path))


if __name__ == "__main__":
    unittest.main()
