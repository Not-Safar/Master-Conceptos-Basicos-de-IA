"""Empaqueta únicamente código, corpus y evidencias CC0 revisadas; nunca el entorno local."""
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
TOP_FILES = ["README.md", "REPORT.md", "CORPUS_LICENSE.md", "requirements.txt",
             "requirements-dev.txt", "requirements-lock.txt", ".env.example", ".gitignore",
             "start-api.ps1", "start-ui.ps1", "start-app.ps1", "restart-app.ps1"]
EVIDENCE = ["README.md", "VALIDATION.md", "evaluation.json", "persistence-check.json",
            "persistence-before.json", "persistence-after.json", "persistence-process.json",
            "corpus-streamlit-answer.jpg", "corpus-api-answer.jpg", "corpus-streamlit-abstention.jpg",
            "delivery-check.json"]

def main():
    files = [ROOT / name for name in TOP_FILES]
    for folder, pattern in [("app", "*.py"), ("ui", "*.py"), ("tests", "*.py"),
                            ("scripts", "*.py"), ("data", "*.md"), (".streamlit", "*.toml")]:
        files.extend(sorted((ROOT / folder).rglob(pattern)))
    files.extend(ROOT / "evidence" / name for name in EVIDENCE)
    files.append(ROOT / "output/pdf/reporte-aula-rag.pdf")
    files = sorted(set(files))
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(f"Falta un archivo de entrega: {path.relative_to(ROOT)}")
        if any(part in {"__pycache__", ".venv", "chroma", "logs", "uploads"} for part in path.relative_to(ROOT).parts):
            raise ValueError("Un archivo no permitido entró en la selección")
        if path.suffix.lower() in {".py", ".md", ".json", ".txt", ".toml", ".ps1", ".example"}:
            content = path.read_text(encoding="utf-8-sig")
            if re.search(r"AIza[0-9A-Za-z_-]{30,}", content):
                raise ValueError(f"Posible clave de Google en {path.name}")
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8-sig")
    if not re.search(r"^GOOGLE_API_KEY=\s*$", env_example, re.MULTILINE):
        raise ValueError("La clave de .env.example debe estar vacía")
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    target = output / "aula-rag-entrega.zip"
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, "proyecto_final/rag-app/" + path.relative_to(ROOT).as_posix())
    with ZipFile(target) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert not any(Path(name).name == ".env" for name in names)
        assert sum(name.startswith("proyecto_final/rag-app/data/") for name in names) == 5
    manifest = {"archive": target.name, "files": len(files), "bytes": target.stat().st_size,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "google_api_key_example_empty": True, "zip_integrity_ok": True,
                "excluded": [".env", ".venv", "chroma", "logs", "caches", "personal PDF evidence"],
                "entries": names}
    (output / "delivery-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "entries"}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
