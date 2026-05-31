"""Script para regenerar DOCUMENTO_TECNICO.md a partir del código.

Uso:
    python scripts/generate_docs.py

Escanea app/models/, app/services/, tests/, alembic/, pyproject.toml
y reconstruye la parte técnica de la documentación.
"""

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

PROJECT_ROOT = Path(__file__).parents[1]
OUTPUT = PROJECT_ROOT / "DOCUMENTO_TECNICO.md"


def read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def get_models(path: Path) -> list[dict]:
    """Parse app/models/*.py and extract entity definitions."""
    models = []
    for f in sorted(path.glob("*.py")):
        if f.name == "__init__.py" or f.name == "base.py":
            continue
        source = f.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Call):
                        name = base.func.id if isinstance(base.func, ast.Name) else ""
                    elif isinstance(base, ast.Name):
                        name = base.id
                    else:
                        name = ""
                    if "AuditMixin" in name or name == "AuditMixin":
                        break
                else:
                    continue

                fields = []
                relationships = []
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        col_name = item.target.id
                        if col_name in ("id", "created_at", "updated_at", "deleted_at"):
                            continue

                        dump = ast.dump(item)

                        if "back_populates" in dump:
                            rel_match = re.search(
                                r"value='(\w+)'", dump[dump.index("back_populates") :]
                            )
                            target = rel_match.group(1) if rel_match else "?"
                            is_list = "List" in (
                                ast.unparse(item.annotation) if item.annotation else ""
                            )
                            has_uselist = "uselist" in dump
                            is_one_to_one = has_uselist and "False" in dump[dump.index("uselist") :]
                            rel_type = "1:1" if (not is_list or is_one_to_one) else "1:N"
                            relationships.append(
                                {
                                    "name": col_name,
                                    "target": target,
                                    "relationship": rel_type,
                                }
                            )
                            continue

                        col_type = ast.unparse(item.annotation) if item.annotation else "?"
                        is_optional = "Optional" in col_type
                        nullable = "nullable=True" in dump if item.value else False
                        fk_match = re.search(r"foreign_key.*?value='([^']+)'", dump)
                        has_fk = fk_match.group(1) if fk_match else None

                        fields.append(
                            {
                                "name": col_name,
                                "type": col_type,
                                "nullable": is_optional or nullable,
                                "fk": has_fk,
                            }
                        )

                if fields or relationships:
                    models.append(
                        {
                            "name": node.name,
                            "fields": fields,
                            "relationships": relationships,
                            "file": f.name,
                        }
                    )
    return models


def get_services(path: Path) -> list[dict]:
    """Parse app/services/*.py and extract service methods."""
    services = []
    for f in sorted(path.glob("*.py")):
        if f.name == "__init__.py":
            continue
        source = f.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        args = [a.arg for a in item.args.args if a.arg != "self"]
                        doc = ast.get_docstring(item)
                        returns = ast.unparse(item.returns) if item.returns else None
                        methods.append(
                            {
                                "name": item.name,
                                "args": args,
                                "returns": returns,
                                "doc": doc,
                            }
                        )
                if methods:
                    services.append({"name": node.name, "methods": methods})
    return services


def get_tests(path: Path) -> list[dict]:
    """Parse tests/*.py and extract test classes and methods."""
    tests = []
    for f in sorted(path.glob("*.py")):
        if f.name in ("__init__.py", "conftest.py"):
            continue
        source = f.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                        doc = ast.get_docstring(item)
                        methods.append({"name": item.name, "doc": doc})
                if methods:
                    tests.append(
                        {
                            "file": f.name,
                            "class": node.name,
                            "methods": methods,
                        }
                    )
    return tests


def get_migrations(path: Path) -> list[dict]:
    """Parse alembic/versions/*.py and extract migration info."""
    migrations = []
    for f in sorted(path.glob("*.py")):
        source = f.read_text(encoding="utf-8")
        doc_match = re.search(r'"""(.+?)"""', source, re.DOTALL)
        doc = doc_match.group(1).strip().split("\n")[0] if doc_match else f.stem
        rev_match = re.search(r'revision:\s*str\s*=\s*["\'](.+?)["\']', source)
        rev = rev_match.group(1) if rev_match else "?"
        down_rev = ""
        dr_match = re.search(r"down_revision.*?=.*?['\"](.*?)['\"]", source)
        if dr_match:
            down_rev = dr_match.group(1)

        tables_added = []
        for m in re.finditer(r"create_table\('(.+?)'\)", source):
            tables_added.append(m.group(1))

        migrations.append(
            {
                "revision": rev,
                "down_revision": down_rev,
                "doc": doc,
                "tables_added": tables_added,
            }
        )
    return migrations


def get_pyproject() -> dict:
    """Parse pyproject.toml for dependencies."""
    content = read_file(PROJECT_ROOT / "pyproject.toml")
    deps = re.findall(r'"(.*?)>=', content)
    dev_deps = []
    in_dev = False
    for line in content.splitlines():
        if "[project.optional-dependencies]" in line:
            in_dev = True
            continue
        if in_dev and "]" in line and "=" not in line:
            in_dev = False
        if in_dev and ">=" in line:
            m = re.search(r'"(.*?)>=', line)
            if m:
                dev_deps.append(m.group(1))
    return {"deps": deps, "dev_deps": dev_deps}


def generate() -> str:
    models_dir = PROJECT_ROOT / "app" / "models"
    services_dir = PROJECT_ROOT / "app" / "services"
    tests_dir = PROJECT_ROOT / "tests"
    alembic_versions = PROJECT_ROOT / "alembic" / "versions"

    models = get_models(models_dir)
    services = get_services(services_dir)
    tests = get_tests(tests_dir)
    migrations = get_migrations(alembic_versions)
    pyproject = get_pyproject()

    lines = []
    a = lines.append

    a("# Documento Técnico — rental-mgmt")
    a("")
    a("> Generado automáticamente por `scripts/generate_docs.py`. No editar manualmente.")
    a("")

    # ── Stack ──
    a("## 1. Stack tecnológico")
    a("")
    a("| Capa | Tecnología |")
    a("|---|---|")
    a("| Runtime | Python ≥ 3.11 |")
    if pyproject["deps"]:
        a(f"| Dependencias principales | {', '.join(pyproject['deps'])} |")
    if pyproject["dev_deps"]:
        a(f"| Dependencias de desarrollo | {', '.join(pyproject['dev_deps'])} |")
    a("")

    # ── Estructura ──
    a("## 2. Estructura del proyecto")
    a("")
    a("```")
    for line in _tree(PROJECT_ROOT, "rental-mgmt"):
        a(line)
    a("```")
    a("")

    # ── Modelos ──
    a("## 3. Modelos de datos (SQLModel)")
    a("")
    a("Todas las entidades heredan de `AuditMixin` que aporta:")
    a("- `id`: Integer, PK, autoincrement")
    a("- `created_at`: DateTime, default UTC now")
    a("- `updated_at`: DateTime, default UTC now")
    a("- `deleted_at`: DateTime | None (soft-delete)")
    a("")

    if models:
        for m in models:
            a(f"### {m['name']} (`{m['file']}`)")
            a("")
            if m["fields"]:
                a("| Campo | Tipo | Nulo | FK |")
                a("|---|---|---|---|")
                for f in m["fields"]:
                    fk_str = f"→ `{f['fk']}`" if f["fk"] else ""
                    nullable_str = "Sí" if f["nullable"] else "No"
                    a(f"| `{f['name']}` | {f['type']} | {nullable_str} | {fk_str} |")
                a("")
            if m["relationships"]:
                a("**Relaciones:**")
                for r in m["relationships"]:
                    a(f"- `{r['name']}` → {r['relationship']} → `{r['target']}`")
                a("")

    # ── Servicios ──
    a("## 4. Servicios")
    a("")
    if services:
        for svc in services:
            a(f"### {svc['name']}")
            a("")
            for method in svc["methods"]:
                args_str = ", ".join([f"`{a}`" for a in method["args"]])
                returns_str = f" → `{method['returns']}`" if method["returns"] else ""
                a(f"- **{method['name']}**({args_str}){returns_str}")
                if method["doc"]:
                    doc_short = method["doc"].strip().split("\n")[0]
                    a(f"  - {doc_short}")
                    extra_lines = method["doc"].strip().split("\n")[1:]
                    for el in extra_lines:
                        a(f"  {el}")
            a("")
    else:
        a("*(No hay servicios implementados)*")
        a("")

    # ── Tests ──
    a("## 5. Tests")
    a("")
    a(f"**Total: {sum(len(t['methods']) for t in tests)} tests**")
    a("")

    if any(f.name == "conftest.py" for f in tests_dir.glob("*.py")):
        a("### Fixtures")
        a("")
        conftest = read_file(tests_dir / "conftest.py")
        for m in re.finditer(r"def (\w+)\(.*?\)(.*?)(?=\ndef |\Z)", conftest, re.DOTALL):
            name = m.group(1)
            if name.startswith("test_"):
                continue
            doc_match = re.search(r'"""(.*?)"""', m.group(2), re.DOTALL)
            doc = doc_match.group(1).strip() if doc_match else ""
            first_line = doc.split("\n")[0] if doc else ""
            a(f"- `{name}`: {first_line}" if first_line else f"- `{name}`")
        a("")

    if tests:
        for t in tests:
            a(f"### {t['file']} — {t['class']}")
            a("")
            a("| Test | Descripción |")
            a("|---|---|")
            for method in t["methods"]:
                doc = method["doc"] or ""
                desc = doc.strip().split("\n")[0] if doc else ""
                a(f"| `{method['name']}` | {desc} |")
            a("")

    # ── Migraciones ──
    a("## 6. Migraciones (Alembic)")
    a("")
    if migrations:
        for m in migrations:
            a(f"- **`{m['revision'][:8]}`** → {m['doc']}")
            if m["tables_added"]:
                a(f"  - Tablas: {', '.join(f'`{t}`' for t in m['tables_added'])}")
            if m["down_revision"]:
                a(f"  - Padre: `{m['down_revision'][:8]}`")
    a("")
    a("```bash")
    a("alembic upgrade head    # Aplicar pendientes")
    a("alembic downgrade -1   # Revertir última")
    a("alembic history        # Ver historial")
    a("```")
    a("")

    # ── Comandos útiles ──
    a("## 7. Comandos útiles")
    a("")
    a("```bash")
    a("pytest -v                  # Ejecutar tests")
    a("ruff check .               # Lint")
    a("ruff check --fix .         # Auto-fix")
    a("python -m app.seed         # Cargar datos de prueba")
    a("python scripts/generate_docs.py  # Regenerar este documento")
    a("```")
    a("")

    return "\n".join(lines)


def _tree(root: Path, prefix: str, max_depth: int = 3) -> list[str]:
    """Generate a simple ASCII tree of the project structure."""
    lines = [f"{prefix}/"]

    # Directories and files to include
    include_dirs = {"app", "tests", "alembic", "scripts", "data"}
    exclude_dirs = {"__pycache__", ".git", ".ruff_cache", ".pytest_cache", ".opencode"}
    exclude_files = {"__init__.py", ".gitkeep"}

    def _walk(dir_path: Path, depth: int = 0) -> list[str]:
        result = []
        if depth > max_depth:
            return result

        indent = "    " * depth
        entries = sorted(
            dir_path.iterdir(),
            key=lambda x: (not x.is_dir(), x.name),
        )
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "

            if entry.is_dir():
                if depth == 0 and entry.name not in include_dirs:
                    continue
                if entry.name in exclude_dirs:
                    continue
                result.append(f"{indent}{connector}{entry.name}/")
                result.extend(_walk(entry, depth + 1))
            else:
                if entry.name in exclude_files:
                    continue
                if entry.suffix in (".pyc",):
                    continue
                result.append(f"{indent}{connector}{entry.name}")
        return result

    lines.extend(_walk(root, 0))
    return lines


def main():
    content = generate()
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"✅ Documento generado: {OUTPUT}")


if __name__ == "__main__":
    main()
