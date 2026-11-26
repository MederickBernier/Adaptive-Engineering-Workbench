"""
Integration tests for AEW's read-only Git adapter.

Tests use isolated temporary Git repositories.

Run:
    python -m pytest tests/integration/test_git_repository.py -v

Requirements:
    Python 3.11+
    pytest
    Git executable available on PATH

The adapter must not modify Git or workspace state.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
from jsonschema import Draft202012Validator

from engine.brain.discovery import discover
from engine.brain.model import Assertion, Depth, Evidence, Revision, Verification
from engine.brain.retrieval import retrieve
from engine.brain.store import ProjectBrain, assertion_id
from engine.config import load_config
from engine.context.assembly import assemble_context
from engine.context.package import ContextPackage, ContextPackageError
from engine.delivery.draft import review_digest
from engine.delivery.proposal import UnitDelivery, propose_commit
from engine.delivery.verification import DeliveryError
from engine.execution.authority import (
    ExecutionDenied,
    GrantVerifier,
    TrustedGrantIssuer,
)
from engine.execution.changes import TextReplacement, prepare_changes
from engine.execution.checkpoint import CheckpointStore
from engine.execution.controller import ExecutionController
from engine.execution.envelope import (
    ExecutionBudget,
    ExecutionEnvelope,
    ExecutionPolicy,
    observe_workspace,
)
from engine.execution.isolated import DockerSandbox
from engine.git.preflight import GitPreflight
from engine.git.repository import (
    GitCommandError,
    GitRepository,
    RepositoryNotFoundError,
    WorkspaceState,
)
from engine.planning.assessment import Level, assess
from engine.planning.history import PlanHistory
from engine.planning.plan import Task, WorkUnit, build_plan
from engine.workflow.host import TaskHost
from engine.workflow.intake import Intake, plan_task


def git(
    repository: Path,
    *arguments: str,
) -> str:
    """Execute Git inside a disposable test repository."""

    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=15,
    )

    return result.stdout.strip()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Create an isolated repository with one commit."""

    if shutil.which("git") is None:
        pytest.skip("Git executable is unavailable")

    root = tmp_path / "repository"
    root.mkdir()

    git(root, "init", "-b", "master")

    git(root, "config", "user.name", "AEW Test")
    git(root, "config", "user.email", "aew@example.invalid")

    (root / "README.md").write_text(
        "# Test Repository\n",
        encoding="utf-8",
    )

    git(root, "add", "README.md")
    git(root, "commit", "-m", "Initial commit")

    return root


def test_project_brain_discovers_pinned_regions(
    repository: Path, tmp_path: Path
) -> None:
    committed = {
        "backend/app.py": "print('hello')",
        "backend/pyproject.toml": '[project]\ndependencies = ["fastapi", "pytest"]\n'
        "[tool.ruff]\nline-length = 100\n",
        "frontend/app.ts": "export const value = 1;",
        "frontend/package.json": '{"dependencies": {"react": "*"}}',
        "frontend/package-lock.json": "{}",
        ".github/workflows/ci.yml": "name: CI",
    }
    for path, content in committed.items():
        file = repository / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Add discovery inputs")
    manifest = repository / "backend/pyproject.toml"
    manifest.write_text('[project]\ndependencies = ["django"]\n', encoding="utf-8")

    adapter = GitRepository(repository)
    brain = ProjectBrain(tmp_path / "brain.sqlite3", adapter.root.as_uri())
    broad = discover(adapter, brain)
    backend = discover(
        adapter, brain, commit=broad.revision.commit, regions=("backend",)
    )

    facts = {(item.relation, item.target) for item in broad.assertions}
    assert {
        ("language", "Python"),
        ("language", "TypeScript"),
        ("framework", "FastAPI"),
        ("framework", "React"),
        ("package_manager", "npm"),
        ("test_tool", "pytest"),
        ("continuous_integration", "GitHub Actions"),
        ("format_convention", "Ruff line length 100"),
    } <= facts
    assert ("framework", "Django") not in facts
    assert backend.regions == ("backend",)
    assert all(
        evidence.path and evidence.path.startswith("backend/")
        for item in backend.assertions
        for evidence in item.evidence
    )
    assert any(item.depth == Depth.STRUCTURAL for item in backend.assertions)
    assert brain.load(broad.id) == broad


def test_brain_retrieval_invalidates_changed_regions_and_dependents(
    repository: Path, tmp_path: Path
) -> None:
    for region in ("api", "storage", "ui"):
        file = repository / region / "source.py"
        file.parent.mkdir()
        file.write_text(f"# {region}", encoding="utf-8")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Establish component evidence")
    adapter = GitRepository(repository)
    old_commit = git(repository, "rev-parse", "HEAD")
    revision = Revision(adapter.root.as_uri(), old_commit)
    path = tmp_path / "brain.sqlite3"
    brain = ProjectBrain(path, revision.repository)

    def assertion(region: str, relation: str, target: str, depth: Depth) -> Assertion:
        return Assertion(
            revision,
            region,
            relation,
            target,
            (
                Evidence(
                    f"git:{old_commit}:{region}/source.py",
                    "Inspected source",
                    f"{region}/source.py",
                ),
            ),
            region,
            depth,
        )

    dependency = assertion("api", "depends_on", "storage", Depth.STRUCTURAL)
    api = assertion("api", "handles", "requests", Depth.BEHAVIORAL)
    storage = assertion("storage", "maintains", "data", Depth.SEMANTIC)
    ui = assertion("ui", "renders", "pages", Depth.DISCOVERY)
    snapshot = brain.publish(
        revision, ("api", "storage", "ui"), (dependency, api, storage, ui)
    )
    git(repository, "mv", "storage/source.py", "storage/renamed.py")
    git(repository, "commit", "-m", "Rename storage evidence")
    new_commit = git(repository, "rev-parse", "HEAD")

    reopened = ProjectBrain(path, revision.repository)
    assert reopened.snapshot_ids(old_commit) == (snapshot.id,)
    view = retrieve(adapter, reopened, snapshot.id, target_commit=new_commit)
    assert view.revision.commit == new_commit
    assert view.changed_paths == ("storage/renamed.py", "storage/source.py")
    assert view.affected_regions == ("api", "storage")
    assert view.current == (ui,)
    assert set(view.stale) == {dependency, api, storage}
    assert storage.depth is Depth.SEMANTIC
    assert retrieve(adapter, reopened, snapshot.id).stale == ()
    assert retrieve(
        adapter, reopened, snapshot.id, target_commit=new_commit, region="ui"
    ).current == (ui,)
    assert reopened.load(snapshot.id) == snapshot


def test_context_assembly_selects_provenance_and_reconciles_explicitly(
    repository: Path, tmp_path: Path
) -> None:
    for name in ("api", "storage", "unrelated"):
        source = repository / name / "source.py"
        source.parent.mkdir()
        source.write_text(f"# {name}", encoding="utf-8")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Create context inputs")
    adapter = GitRepository(repository)
    old_commit = git(repository, "rev-parse", "HEAD")
    revision = Revision(adapter.root.as_uri(), old_commit)
    brain = ProjectBrain(tmp_path / "brain.sqlite3", revision.repository)

    def claim(subject, relation, target, verification=Verification.VERIFIED):
        path = f"{subject}/source.py"
        return Assertion(
            revision,
            subject,
            relation,
            target,
            (Evidence(f"git:{old_commit}:{path}", "Inspected committed source", path),),
            subject,
            Depth.STRUCTURAL,
            verification=verification,
        )

    direct = claim("api", "depends_on", "storage")
    provisional = claim("api", "uses", "optional caching", Verification.PROVISIONAL)
    related = claim("storage", "contract", "storage interface")
    unrelated = claim("unrelated", "language", "Python")
    snapshot = brain.publish(
        revision,
        ("api", "storage", "unrelated"),
        (direct, provisional, related, unrelated),
    )
    options = {"task_id": "task-1", "branch": "master", "region": "api"}
    package = assemble_context(
        adapter, brain, snapshot.id, commit=old_commit, **options
    )
    document = package.to_dict()
    schema = Path(__file__).resolve().parents[2] / "contracts" / "context.schema.json"
    Draft202012Validator(json.loads(schema.read_bytes())).validate(document)
    entries = {item["id"]: item for item in document["knowledge"]["assertions"]}
    assert set(entries) == {
        assertion_id(item) for item in (direct, provisional, related)
    }
    assert entries[assertion_id(related)]["relevance"] == "related"
    assert entries[assertion_id(provisional)]["verification"] == "provisional"
    assert entries[assertion_id(direct)]["evidence"][0]["revision"] == old_commit
    assert ContextPackage.from_json(package.to_json()) == package
    assert (
        assemble_context(adapter, brain, snapshot.id, commit=old_commit, **options)
        == package
    )

    budget = len(package.to_json()) - 200
    bounded = assemble_context(
        adapter, brain, snapshot.id, commit=old_commit, max_bytes=budget, **options
    )
    assert len(bounded.to_json()) <= budget
    assert 0 < len(bounded.to_dict()["knowledge"]["assertions"]) < len(entries)
    assert any(
        "budget" in text for text in bounded.to_dict()["integrity"]["limitations"]
    )
    with pytest.raises(ContextPackageError, match="smaller than required metadata"):
        assemble_context(
            adapter, brain, snapshot.id, commit=old_commit, max_bytes=1, **options
        )

    (repository / "storage/source.py").write_text("# modified", encoding="utf-8")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Change dependency evidence")
    new_commit = git(repository, "rev-parse", "HEAD")
    with pytest.raises(ContextPackageError, match="explicit reconciliation"):
        assemble_context(adapter, brain, snapshot.id, commit=new_commit, **options)
    reconciled = assemble_context(
        adapter, brain, snapshot.id, commit=new_commit, reconcile=True, **options
    )
    assert reconciled.to_dict()["identity"]["revision"]["commit"] == new_commit
    assert reconciled.to_dict()["integrity"]["freshness"] == "stale"
    assert all(
        item["verification"] == "stale"
        for item in reconciled.to_dict()["knowledge"]["assertions"]
    )
    assert package.to_dict() == document


def test_context_assembly_requires_fingerprint_for_dirty_preflight(
    repository: Path, tmp_path: Path
) -> None:
    adapter = GitRepository(repository)
    brain = ProjectBrain(tmp_path / "brain.sqlite3", adapter.root.as_uri())
    snapshot = discover(adapter, brain)
    (repository / "uncommitted.txt").write_text("uncommitted", encoding="utf-8")
    report = GitPreflight(adapter, load_config(repository)).inspect(
        task_type="fix", issue="1", title="Example", intended_scope=["README.md"]
    )
    options = {
        "task_id": "task-1",
        "branch": "master",
        "region": ".",
        "commit": snapshot.revision.commit,
        "preflight": report,
    }
    with pytest.raises(ContextPackageError, match="requires a workspace fingerprint"):
        assemble_context(adapter, brain, snapshot.id, **options)
    package = assemble_context(
        adapter, brain, snapshot.id, workspace_fingerprint="worktree-hash", **options
    )
    assert (
        package.to_dict()["identity"]["revision"]["workspace_fingerprint"]
        == "worktree-hash"
    )
    assert "uncommitted.txt" not in package.to_json().decode()


@pytest.fixture
def guarded_execution(repository: Path, tmp_path: Path):
    (repository / "src").mkdir()
    for name in ("public.py", "private.py"):
        (repository / "src" / name).write_bytes(b"# example\n")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Add guarded fixture files")
    adapter = GitRepository(repository)
    workspace, fingerprint = observe_workspace(adapter)
    brain = ProjectBrain(tmp_path / "brain.sqlite3", workspace.repository)
    snapshot = discover(adapter, brain, regions=("src",))
    task = Task("m5-test", workspace.repository, "Read fixture", ("Record evidence",))
    context = assemble_context(
        adapter,
        brain,
        snapshot.id,
        task_id=task.id,
        branch=workspace.branch,
        commit=workspace.commit,
        region="src",
    )
    history = PlanHistory(brain)
    draft = build_plan(
        task,
        assess(risk=Level.LOW, uncertainty=Level.HIGH, rationale="Inspect fixture"),
        approach="Read committed evidence",
        scope=("src/**",),
        verification=("Stop when evidence is recorded",),
        work_units=(
            WorkUnit(
                "unit-1",
                "Read source",
                ("src/**",),
                task.acceptance,
                ("Compare source to recorded object",),
                commit_required=False,
            ),
        ),
        context=context,
        review_questions=("What does the source declare?",),
        investigation_budget=3,
    )
    revision = history.append(draft)
    now = datetime.now(UTC)
    key = b"a" * 32
    signed = TrustedGrantIssuer("engineer", key).issue(
        task_id=task.id,
        plan_revision=revision.revision,
        workspace=workspace,
        work_units=("unit-1",),
        operations=("investigate", "implement"),
        allowed_paths=("src/**",),
        protected_paths=("src/private.py",),
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    envelope = ExecutionEnvelope(
        "test-execution",
        task.id,
        revision.revision,
        "unit-1",
        context.package_id,
        snapshot.id,
        signed.grant.grant_id,
        workspace,
        fingerprint,
        ("investigate", "implement"),
        ("src/**",),
        ExecutionBudget(4, 4, 120),
    )
    policy = ExecutionPolicy(
        adapter, history, GrantVerifier("engineer", key, is_revoked=lambda _: False)
    )
    return adapter, context, history, draft, signed, envelope, policy


def test_execution_policy_denies_protected_expanded_or_unsupported_access(
    guarded_execution,
):
    _, context, _, _, signed, envelope, policy = guarded_execution
    policy.authorize(
        envelope, context, signed, operation="investigate", path="src/public.py"
    )
    with pytest.raises(ExecutionDenied, match="protected"):
        policy.authorize(
            envelope, context, signed, operation="investigate", path="src/private.py"
        )
    expanded = replace(envelope, allowed_paths=("src/**", "README.md"))
    with pytest.raises(ExecutionDenied, match="expands beyond"):
        policy.authorize(
            expanded, context, signed, operation="investigate", path="src/public.py"
        )
    with pytest.raises(ExecutionDenied, match="no supported guarded adapter"):
        policy.authorize(
            envelope, context, signed, operation="implement", path="src/public.py"
        )


def test_execution_policy_rechecks_workspace_and_plan(guarded_execution):
    adapter, context, history, draft, signed, envelope, policy = guarded_execution
    unrelated = adapter.root / "unrelated.txt"
    unrelated.write_text("preserve this edit", encoding="utf-8")
    with pytest.raises(ExecutionDenied, match="clean, attached"):
        policy.authorize(
            envelope, context, signed, operation="investigate", path="src/public.py"
        )
    assert unrelated.read_text(encoding="utf-8") == "preserve this edit"
    unrelated.unlink()
    history.append(
        replace(draft, approach="Reconsider the investigation"), expected_revision=1
    )
    with pytest.raises(ExecutionDenied, match="superseded"):
        policy.authorize(
            envelope, context, signed, operation="investigate", path="src/public.py"
        )


def test_workflow_denies_isolated_operations_for_explore_or_unresolved_preflight(
    guarded_execution, tmp_path
):
    adapter, context, history, draft, signed, envelope, _ = guarded_execution
    host = TaskHost(
        adapter,
        history,
        GrantVerifier("engineer", b"a" * 32, is_revoked=lambda _: False),
        CheckpointStore(tmp_path / "workflow.sqlite3"),
    )
    with pytest.raises(ExecutionDenied, match="limited to read-only"):
        host.verify(envelope, context, signed, replacements=(), check="check")
    standard = build_plan(
        draft.task,
        assess(risk=Level.MODERATE, uncertainty=Level.LOW, rationale="Review fixture"),
        approach="Review edit",
        scope=draft.scope,
        work_units=(replace(draft.work_units[0], commit_required=True),),
        context=context,
    )
    revision = history.append(standard, expected_revision=1)
    with pytest.raises(ExecutionDenied, match="Resolve mandatory preflight"):
        host.draft(
            task_id=draft.task.id,
            revision=revision.revision,
            units=(),
            base_branch="master",
            head_branch="example",
        )


def test_guarded_read_resumes_without_replay_or_budget_reset(
    guarded_execution, tmp_path: Path
):
    adapter, context, history, _, signed, envelope, _ = guarded_execution
    envelope = replace(envelope, budget=ExecutionBudget(2, 2, 120))
    path = "src/public.py"
    expected = adapter.committed_files(envelope.workspace.commit, path)[0].oid
    checkpoint_path = tmp_path / "execution.sqlite3"
    store = CheckpointStore(checkpoint_path)
    original_repo = adapter.snapshot()
    abandoned = store.reserve(envelope, path, expected)
    reopened = CheckpointStore(checkpoint_path)
    controller = TaskHost(
        adapter,
        history,
        GrantVerifier("engineer", b"a" * 32, is_revoked=lambda _: False),
        reopened,
    )
    with pytest.raises(ExecutionDenied, match="explicit checkpoint resumption"):
        controller.read(envelope, context, signed, path=path, expected_oid=expected)
    new_file = adapter.root / "interruption.txt"
    new_file.write_text("external edit", encoding="utf-8")
    with pytest.raises(ExecutionDenied, match="clean, attached"):
        controller.resume_read(envelope, context, signed)
    assert reopened.load(envelope).tool_calls == 1
    new_file.unlink()
    controller.resume_read(envelope, context, signed)
    assert reopened.load(envelope).tool_calls == 1
    evidence = controller.read(
        envelope, context, signed, path=path, expected_oid=expected
    )
    assert evidence.content == "# example\n"
    assert evidence.oid == expected
    with pytest.raises(ExecutionDenied, match="superseded"):
        store.finish(envelope, abandoned, success=True)
    with pytest.raises(ExecutionDenied, match="budget is exhausted"):
        controller.read(envelope, context, signed, path=path, expected_oid=expected)
    assert reopened.load(envelope).reason == "budget"
    with pytest.raises(ExecutionDenied, match="budget is exhausted"):
        controller.resume_read(envelope, context, signed)
    assert adapter.snapshot() == original_repo


def test_guarded_read_rejects_mismatched_file_version(
    guarded_execution, tmp_path: Path
):
    adapter, context, _, _, signed, envelope, policy = guarded_execution
    store = CheckpointStore(tmp_path / "execution.sqlite3")
    controller = ExecutionController(adapter, policy, store)
    path = "src/public.py"
    with pytest.raises(ExecutionDenied, match="exact committed file version"):
        controller.read(envelope, context, signed, path=path, expected_oid="f" * 40)
    assert store.load(envelope).reason == "tool_failure"
    assert store.load(envelope).tool_calls == 1
    with pytest.raises(ExecutionDenied, match="exact committed file version"):
        controller.resume(envelope, context, signed)


@pytest.fixture
def implementation_execution(guarded_execution, tmp_path, monkeypatch):
    adapter, _, _, draft, signed, envelope, policy = guarded_execution
    commit = envelope.workspace.commit
    monkeypatch.setattr(
        adapter, "remote_default_branch", lambda *_args, **_kwargs: "master"
    )
    monkeypatch.setattr(
        adapter, "integration_branch_commit", lambda *_args, **_kwargs: commit
    )
    monkeypatch.setattr(
        adapter,
        "remote_branch_commit",
        lambda branch, **_kwargs: commit if branch == "master" else None,
    )
    monkeypatch.setattr(
        adapter, "github_remote_repository", lambda _: "example/project"
    )
    provider = Mock(repository="example/project")
    provider.open_pull_requests.return_value = ()
    brain = ProjectBrain(tmp_path / "brain.sqlite3", adapter.root.as_uri())
    result = plan_task(
        adapter,
        brain,
        Intake(
            draft.task,
            assess(
                risk=Level.MODERATE,
                uncertainty=Level.LOW,
                rationale="A bounded text replacement",
            ),
            approach="Review a replacement",
            task_type="fix",
            region="src",
            scope=("src/**",),
            verification=("Compare source to recorded object",),
            work_units=(replace(draft.work_units[0], commit_required=True),),
            expected_revision=1,
        ),
        github=provider,
        verify_remote=True,
    )
    assert result.state == "awaiting_approval"
    revision, context = result.revision, result.context
    signed = TrustedGrantIssuer("engineer", b"a" * 32).issue(
        task_id=draft.task.id,
        plan_revision=revision.revision,
        workspace=envelope.workspace,
        work_units=("unit-1",),
        operations=("implement", "run_tests"),
        allowed_paths=("src/**",),
        protected_paths=signed.grant.protected_paths,
        issued_at=signed.grant.issued_at,
        expires_at=signed.grant.expires_at,
    )
    envelope = replace(
        envelope,
        plan_revision=revision.revision,
        grant_id=signed.grant.grant_id,
        operations=("implement", "run_tests"),
        context_id=context.package_id,
        snapshot_id=context.to_dict()["identity"]["revision"]["snapshot_id"],
    )
    return adapter, context, signed, envelope, policy, revision


def test_scoped_change_review_preserves_shared_checkout(implementation_execution):
    adapter, context, signed, envelope, policy, _ = implementation_execution
    path = "src/public.py"
    oid = adapter.committed_files(envelope.workspace.commit, path)[0].oid
    before = adapter.snapshot()
    review = prepare_changes(
        adapter,
        policy,
        envelope,
        context,
        signed,
        (TextReplacement(path, oid, "# reviewed\n"),),
    )
    assert "-# example" in review.diff and "+# reviewed" in review.diff
    assert len(review.digest) == 64
    assert adapter.snapshot() == before
    assert (adapter.root / path).read_bytes() == b"# example\n"
    with pytest.raises(ExecutionDenied, match="expected committed file version"):
        prepare_changes(
            adapter,
            policy,
            envelope,
            context,
            signed,
            (TextReplacement(path, "f" * 40, "different"),),
        )


@pytest.mark.skipif(
    not os.environ.get("AEW_TEST_DOCKER_IMAGE"),
    reason="requires a pinned local Docker image",
)
def test_isolated_check_materializes_review_without_host_access(
    implementation_execution, tmp_path
):
    adapter, context, signed, envelope, _, _ = implementation_execution
    executable = shutil.which("docker")
    assert executable is not None
    sandbox = DockerSandbox(Path(executable), os.environ["AEW_TEST_DOCKER_IMAGE"])
    check = "Compare source to recorded object"
    check_script = (
        "import os, socket; from pathlib import Path; "
        "assert Path('src/public.py').read_bytes() == b'# reviewed\\n'; "
        "assert Path('src/new.py').read_bytes() == b'# new\\n'; "
        "assert not Path('src/private.py').exists(); assert not Path('.git').exists(); "
        "assert not Path('/var/run/docker.sock').exists(); "
        "assert {name for _, name in socket.if_nameindex()} == {'lo'}; "
        "assert os.getuid() == 65534; assert os.statvfs('/').f_flag & os.ST_RDONLY"
    )
    argv = ("/usr/local/bin/python", "-I", "-c", check_script)
    store = CheckpointStore(tmp_path / "isolated.sqlite3")
    history = PlanHistory(
        ProjectBrain(tmp_path / "brain.sqlite3", adapter.root.as_uri())
    )
    verifier = GrantVerifier("engineer", b"a" * 32, is_revoked=lambda _: False)
    controller = TaskHost(
        adapter,
        history,
        verifier,
        store,
        sandbox=sandbox,
        allowed_checks={check: argv, "unrecorded": argv},
    )
    path = "src/public.py"
    oid = adapter.committed_files(envelope.workspace.commit, path)[0].oid
    edits = (
        TextReplacement(path, oid, "# reviewed\n"),
        TextReplacement("src/new.py", None, "# new\n"),
    )
    before = adapter.snapshot()
    with pytest.raises(ExecutionDenied, match="outside the recorded"):
        controller.verify(
            envelope, context, signed, replacements=edits, check="unrecorded"
        )
    result = controller.verify(
        envelope, context, signed, replacements=edits, check=check
    )
    assert result.passed
    assert "+# reviewed" in result.review.diff
    assert adapter.snapshot() == before
    assert (adapter.root / path).read_bytes() == b"# example\n"
    assert not (adapter.root / "src/new.py").exists()
    options = {
        "task_id": envelope.task_id,
        "revision": envelope.plan_revision,
        "units": (
            UnitDelivery(
                envelope,
                result.review,
                "fix: review example",
                "Refresh the example.",
                (result.evidence_id,),
            ),
        ),
        "base_branch": "master",
        "head_branch": "test/example",
    }
    document = controller.draft(**options)
    schema = Path(__file__).resolve().parents[2] / "contracts/delivery.schema.json"
    Draft202012Validator(json.loads(schema.read_bytes())).validate(document)
    assert document["work_units"][0]["verification"][0]["status"] == "passed"
    assert document["pull_request"]["status"] == "proposed"
    assert all(
        item["status"] == "not_authorized" for item in document["publication"].values()
    )
    assert controller.review(reviews=(), **options) == ((), "unit-1")
    review_grant = TrustedGrantIssuer("engineer", b"a" * 32).issue(
        task_id=envelope.task_id,
        plan_revision=envelope.plan_revision,
        workspace=envelope.workspace,
        work_units=("unit-1",),
        operations=("commit",),
        allowed_paths=("src/**",),
        issued_at=signed.grant.issued_at,
        expires_at=signed.grant.expires_at,
        review_digest=review_digest(document, "unit-1"),
    )
    assert controller.review(reviews=(review_grant,), **options) == (("unit-1",), None)
    with pytest.raises(DeliveryError, match="exact sequential checkpoint"):
        controller.review(reviews=(signed,), **options)
    assert adapter.snapshot() == before


@pytest.mark.skipif(
    not os.environ.get("AEW_TEST_DOCKER_IMAGE"),
    reason="requires a pinned local Docker image",
)
def test_isolated_check_removes_timed_out_container():
    executable = shutil.which("docker")
    assert executable is not None
    sandbox = DockerSandbox(Path(executable), os.environ["AEW_TEST_DOCKER_IMAGE"])
    payload = json.dumps(
        {
            "files": {},
            "argv": [
                "/usr/local/bin/python",
                "-I",
                "-c",
                "import time; time.sleep(20)",
            ],
        }
    ).encode()
    with pytest.raises(ExecutionDenied, match="exceeded its deadline"):
        sandbox.run(payload, timeout=2)


def test_delivery_proposal_excludes_unrelated_workspace_changes(
    implementation_execution, tmp_path
):
    adapter, context, signed, envelope, policy, revision = implementation_execution
    path = "src/public.py"
    oid = adapter.committed_files(envelope.workspace.commit, path)[0].oid
    review = prepare_changes(
        adapter,
        policy,
        envelope,
        context,
        signed,
        (TextReplacement(path, oid, "# proposed\n"),),
    )
    (adapter.root / "staged.txt").write_text("stage fixture", encoding="utf-8")
    git(adapter.root, "add", "staged.txt")
    (adapter.root / "untracked.txt").write_text("preserve fixture", encoding="utf-8")
    before = adapter.snapshot()
    proposal = propose_commit(
        adapter,
        CheckpointStore(tmp_path / "delivery.sqlite3"),
        revision,
        UnitDelivery(
            envelope, review, "fix: update example", "Explain the new example."
        ),
    )
    assert proposal["status"] == "not_ready"
    assert [item["path"] for item in proposal["change_boundary"]["files"]] == [path]
    assert "Excluded staged paths: staged.txt" in proposal["commit_proposal"]["body"]
    assert (
        "Excluded unstaged or untracked paths: untracked.txt"
        in proposal["commit_proposal"]["body"]
    )
    assert adapter.snapshot() == before


@pytest.mark.parametrize(
    ("profile", "risk", "uncertainty"),
    [
        ("quick", "low", "low"),
        ("standard", "moderate", "low"),
        ("deep", "high", "low"),
        ("explore", "low", "high"),
    ],
)
def test_task_cli_plans_all_profiles(
    repository, tmp_path, profile, risk, uncertainty, monkeypatch
):
    (repository / "src").mkdir()
    (repository / "src/example.py").write_text("value = 1", encoding="utf-8")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Add planning fixture")
    before = GitRepository(repository).snapshot()
    request = {
        "task": {
            "id": "m7-test",
            "objective": "Review example behavior",
            "acceptance": ["Record behavior"],
        },
        "assessment": {
            "risk": risk,
            "uncertainty": uncertainty,
            "rationale": "Observed fixture",
            "localized": True,
            "acceptance_clear": True,
        },
        "approach": "Inspect the committed example",
        "task_type": "fix",
        "region": "src",
        "scope": ["src/**"],
        "verification": ["Inspect the recorded example"],
    }
    if profile in ("standard", "deep"):
        request["work_units"] = [
            {
                "id": "verify",
                "objective": "Verify fixture",
                "scope": ["src/**"],
                "acceptance": ["Observe report"],
                "verification": ["Inspect fixture"],
                "dependencies": ["inspect"],
            },
            {
                "id": "inspect",
                "objective": "Inspect fixture",
                "scope": ["src/example.py"],
                "acceptance": ["Observe source"],
                "verification": ["Read fixture"],
            },
        ]
    if profile == "explore":
        request.update(questions=["What does the example do?"], investigation_budget=3)
    root = Path(__file__).resolve().parents[2]
    data_home = tmp_path / "data"
    monkeypatch.setenv("LOCALAPPDATA", str(data_home))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    brain_options = (
        [] if profile == "quick" else ["--brain", str(tmp_path / "workflow.sqlite3")]
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "engine.workflow.cli",
            "--repository",
            str(repository),
            *brain_options,
        ],
        cwd=root,
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    output = json.loads(result.stdout)
    if not brain_options:
        assert len(list(data_home.glob("*/projects/*/brain.sqlite3"))) == 1
    document = output["plan"]["task_document"]
    schema = json.loads((root / "contracts/task.schema.json").read_bytes())
    Draft202012Validator(schema).validate(document)
    assert document["assessment"]["profile"] == profile
    assert document["approval"]["status"] == "pending"
    assert output["state"] == (
        "awaiting_approval" if profile == "explore" else "preflight_unresolved"
    )
    if profile in ("standard", "deep"):
        assert [unit["id"] for unit in document["plan"]["work_units"]] == [
            "inspect",
            "verify",
        ]
    assert GitRepository(repository).snapshot() == before


def test_discovery_reuses_pinned_coverage_without_rescanning(
    repository, tmp_path, monkeypatch
):
    adapter = GitRepository(repository)
    database = tmp_path / "brain.sqlite3"
    brain = ProjectBrain(database, adapter.root.as_uri())
    original = discover(adapter, brain, regions=(".", "src"))
    scan = Mock(wraps=adapter.committed_files)
    monkeypatch.setattr(adapter, "committed_files", scan)
    assert (
        discover(
            adapter, ProjectBrain(database, brain.repository), regions=("src", ".")
        )
        == original
    )
    scan.assert_not_called()
    assert discover(adapter, brain, regions=("src",)).id != original.id
    assert scan.call_count == 1
    (repository / "new.py").write_text("answer = 42", encoding="utf-8")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Change committed discovery input")
    assert discover(adapter, brain, regions=(".", "src")).revision != original.revision
    assert scan.call_count == 3


def test_repository_discovery(
    repository: Path,
) -> None:
    """Discover the repository from a nested directory."""

    nested = repository / "src" / "customer"
    nested.mkdir(parents=True)

    adapter = GitRepository(nested)

    assert adapter.root == repository.resolve()
    assert adapter.git_directory.exists()


def test_non_repository_is_rejected(
    tmp_path: Path,
) -> None:
    """Reject paths outside a Git repository."""

    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(RepositoryNotFoundError):
        GitRepository(outside)


def test_clean_repository(
    repository: Path,
) -> None:
    """A committed repository starts clean."""

    adapter = GitRepository(repository)
    snapshot = adapter.snapshot()

    assert snapshot.branch == "master"
    assert snapshot.detached is False
    assert snapshot.workspace_state == WorkspaceState.CLEAN
    assert snapshot.changes == ()

    assert snapshot.head_commit == git(
        repository,
        "rev-parse",
        "HEAD",
    )


def test_unstaged_modification(
    repository: Path,
) -> None:
    """Detect modifications outside the Git index."""

    (repository / "README.md").write_text(
        "# Modified\n",
        encoding="utf-8",
    )

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1

    change = changes[0]

    assert change.path == "README.md"
    assert change.index_status == " "
    assert change.worktree_status == "M"

    assert adapter.workspace_state() == WorkspaceState.DIRTY


def test_staged_modification(
    repository: Path,
) -> None:
    """Detect changes staged in the Git index."""

    (repository / "README.md").write_text(
        "# Staged\n",
        encoding="utf-8",
    )

    git(repository, "add", "README.md")

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1

    assert changes[0].index_status == "M"
    assert changes[0].worktree_status == " "


def test_untracked_file(
    repository: Path,
) -> None:
    """Detect untracked files."""

    (repository / "notes.txt").write_text(
        "Untracked content\n",
        encoding="utf-8",
    )

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1

    assert changes[0].path == "notes.txt"
    assert changes[0].untracked is True


def test_multiple_changes(
    repository: Path,
) -> None:
    """Report staged, unstaged, and untracked changes."""

    (repository / "README.md").write_text(
        "# Modified\n",
        encoding="utf-8",
    )

    (repository / "new.txt").write_text(
        "New file\n",
        encoding="utf-8",
    )

    adapter = GitRepository(repository)

    paths = {change.path for change in adapter.changed_files()}

    assert paths == {
        "README.md",
        "new.txt",
    }


def test_detached_head(
    repository: Path,
) -> None:
    """Recognize a detached HEAD without inventing a branch."""

    git(
        repository,
        "checkout",
        "--detach",
        "HEAD",
    )

    adapter = GitRepository(repository)
    snapshot = adapter.snapshot()

    assert snapshot.branch is None
    assert snapshot.detached is True
    assert snapshot.head_commit is not None


def test_local_branch_discovery(
    repository: Path,
) -> None:
    """List local branches and their commits."""

    git(
        repository,
        "branch",
        "mb/fix/142-null-response",
    )

    adapter = GitRepository(repository)

    branches = {branch.name: branch for branch in adapter.local_branches()}

    assert "master" in branches
    assert "mb/fix/142-null-response" in branches

    assert branches["master"].remote is False
    assert branches["master"].commit == git(
        repository,
        "rev-parse",
        "HEAD",
    )


@pytest.mark.parametrize(
    "branch_name",
    [
        "mb/fix/142-null-response",
        "feature/customer-api",
        "task/123",
        "release/v0.1.0",
    ],
)
def test_valid_branch_names(
    repository: Path,
    branch_name: str,
) -> None:
    """Accept valid Git branch references."""

    adapter = GitRepository(repository)

    assert adapter.is_valid_branch_name(branch_name) is True


@pytest.mark.parametrize(
    "branch_name",
    [
        "",
        "bad branch",
        "../invalid",
        "bad..branch",
        "bad@{branch}",
        "invalid.lock",
        "/absolute",
        "bad//branch",
    ],
)
def test_invalid_branch_names(
    repository: Path,
    branch_name: str,
) -> None:
    """Reject invalid Git branch references."""

    adapter = GitRepository(repository)

    assert adapter.is_valid_branch_name(branch_name) is False


def test_local_branch_collision(
    repository: Path,
) -> None:
    """Detect an existing local task branch."""

    name = "mb/fix/142-null-response"

    git(repository, "branch", name)

    adapter = GitRepository(repository)

    assert adapter.branch_exists(name) is True
    assert adapter.branch_exists("mb/fix/999-other") is False


@pytest.mark.parametrize(
    ("url", "identity"),
    [
        ("https://github.com/example/api.git", "example/api"),
        ("git@github.com:example/api.git", "example/api"),
        ("ssh://git@github.com/example/api", "example/api"),
        ("https://github.com.example.org/example/api.git", None),
    ],
)
def test_github_remote_identity(
    repository: Path, url: str, identity: str | None
) -> None:
    git(repository, "remote", "add", "origin", url)
    assert GitRepository(repository).github_remote_repository("origin") == identity


def test_remote_tracking_branch(
    repository: Path,
    tmp_path: Path,
) -> None:
    """Inspect locally known remote-tracking references."""

    remote = tmp_path / "remote.git"
    remote.mkdir()

    git(remote, "init", "--bare")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/master")

    git(
        repository,
        "remote",
        "add",
        "origin",
        str(remote),
    )

    git(
        repository,
        "push",
        "-u",
        "origin",
        "master",
    )

    git(
        repository,
        "branch",
        "mb/fix/142-null-response",
    )

    git(
        repository,
        "push",
        "origin",
        "mb/fix/142-null-response",
    )

    adapter = GitRepository(repository)

    branches = adapter.remote_branches()

    names = {branch.name for branch in branches}

    assert "origin/master" in names
    assert "origin/mb/fix/142-null-response" in names

    assert adapter.integration_branch_commit("master") == git(
        repository,
        "rev-parse",
        "master",
    )
    before = git(repository, "show-ref")
    commit = git(repository, "rev-parse", "master")
    assert adapter.remote_branch_commit("master") == commit
    git(
        repository,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/stale",
    )
    assert adapter.remote_default_branch() == "stale"
    assert adapter.remote_default_branch(live=True) == "master"
    git(repository, "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
    assert adapter.local_branch_commit("master") == commit
    assert adapter.has_commit(commit)
    assert adapter.remote_branch_commit("missing") is None
    assert adapter.local_branch_commit("missing") is None
    assert not adapter.has_commit("f" * 40)
    with pytest.raises(GitCommandError, match="remote is not configured"):
        adapter.remote_branch_commit("master", remote="missing")
    assert git(repository, "show-ref") == before


def test_renamed_file(
    repository: Path,
) -> None:
    """Parse a staged rename with its original path."""

    git(
        repository,
        "mv",
        "README.md",
        "DOCUMENTATION.md",
    )

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1

    change = changes[0]

    assert change.path == "DOCUMENTATION.md"
    assert change.original_path == "README.md"
    assert change.index_status == "R"


def test_unicode_filename(
    repository: Path,
) -> None:
    """Preserve Unicode filenames in Git status."""

    filename = "données-équipe.txt"

    (repository / filename).write_text(
        "Contenu de test\n",
        encoding="utf-8",
    )

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1
    assert changes[0].path == filename


@pytest.mark.parametrize("status", [b"R ", b"C "])
def test_status_preserves_raw_rename_and_copy_paths(
    repository: Path, monkeypatch: pytest.MonkeyPatch, status: bytes
) -> None:
    adapter = GitRepository(repository)
    output = status + b" destination\r\n.txt\0source-\xff.txt\0"

    def run(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, output, b"")

    monkeypatch.setattr("engine.git.repository.subprocess.run", run)

    (change,) = adapter.changed_files()

    assert change.index_status == chr(status[0])
    assert change.path == "destination\r\n.txt"
    assert change.original_path == "source-\udcff.txt"


@pytest.mark.parametrize(
    ("output", "message"),
    [
        (b"?? file.txt", "Unterminated Git porcelain status entry"),
        (b"R  renamed.txt\0", "Missing rename/copy source path"),
        (b"C  copied.txt\0\0", "Missing rename/copy source path"),
        (b"\0?? file.txt\0", "Unexpected Git porcelain status entry"),
    ],
)
def test_status_rejects_incomplete_records(
    repository: Path, monkeypatch: pytest.MonkeyPatch, output: bytes, message: str
) -> None:
    adapter = GitRepository(repository)

    def run(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, output, b"")

    monkeypatch.setattr("engine.git.repository.subprocess.run", run)

    with pytest.raises(GitCommandError, match=message):
        adapter.changed_files()


def test_adapter_does_not_modify_repository(
    repository: Path,
) -> None:
    """Read-only inspection must preserve Git state."""

    before_head = git(
        repository,
        "rev-parse",
        "HEAD",
    )

    before_status = git(
        repository,
        "status",
        "--porcelain",
    )

    adapter = GitRepository(repository)

    adapter.snapshot()
    adapter.local_branches()
    adapter.remote_branches()
    adapter.branch_exists("mb/fix/142")
    adapter.is_valid_branch_name("mb/fix/142")

    after_head = git(
        repository,
        "rev-parse",
        "HEAD",
    )

    after_status = git(
        repository,
        "status",
        "--porcelain",
    )

    assert before_head == after_head
    assert before_status == after_status


def test_missing_integration_branch(
    repository: Path,
) -> None:
    """Missing remote-tracking baseline returns None."""

    adapter = GitRepository(repository)

    assert adapter.integration_branch_commit("master") is None
