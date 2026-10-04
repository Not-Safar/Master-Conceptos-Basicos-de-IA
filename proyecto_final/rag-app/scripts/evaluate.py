"""Evaluación real por HTTP. Requiere API iniciada y clave válida; consume cuota."""
import argparse
import json
import time
from pathlib import Path

import httpx

CASES = [
    ("¿Qué diferencia hay entre aprendizaje supervisado y no supervisado?", False),
    ("¿Por qué se utiliza solapamiento al dividir los documentos?", False),
    ("¿Cómo se evalúan la recuperación y las citas en un sistema RAG?", False),
    ("¿Cuál es la contraseña del WiFi del salón 302?", True),
    ("¿En qué fecha nació la profesora de este curso?", True),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--ingest", action="store_true", help="Indexa data/ antes de consultar")
    args = parser.parse_args()
    records = []
    target = Path(__file__).resolve().parents[1] / "evidence" / "evaluation.json"
    target.parent.mkdir(exist_ok=True)
    with httpx.Client(base_url=args.url, timeout=300) as client:
        health = client.get("/health")
        health.raise_for_status()
        print(json.dumps(health.json(), ensure_ascii=False, indent=2))
        if args.ingest:
            response = client.post("/ingest", data={"paths": '["."]'})
            response.raise_for_status()
            print("Ingestión:", response.json())
        failures = 0
        for question, expected in CASES:
            attempts = []
            for attempt in range(3):
                started = time.monotonic()
                response = client.post("/query", json={"question": question, "top_k": 4})
                attempts.append({"status_code": response.status_code, "seconds": round(time.monotonic() - started, 2)})
                if response.status_code not in {502, 503, 504} or attempt == 2:
                    break
                print("Reintento por error temporal:", response.status_code, flush=True)
                time.sleep(2 ** attempt)
            if response.is_error:
                records.append({"question": question, "expected_abstained": expected, "passed": False,
                                "attempts": attempts, "error": response.json()})
                target.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
                failures += 1
                continue
            result = response.json()
            passed = result["abstained"] == expected and (expected or bool(result["citations"]))
            failures += not passed
            records.append({"question": question, "expected_abstained": expected, "passed": passed,
                            "attempts": attempts, **result})
            target.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
            print("PASS" if passed else "FAIL", question)
            print(result["answer"])
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Evidencia guardada en {target}. Revisa manualmente exactitud y soporte de cada cita.")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
