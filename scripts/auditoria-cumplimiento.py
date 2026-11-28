#!/usr/bin/env python3
"""
Auditoría automatizada de cumplimiento (policy as code).

Revisa el repositorio contra un conjunto de políticas basadas en:
  - CIS Docker Benchmark v1.6 (sección 4: imágenes y Dockerfiles)
  - CIS Kubernetes Benchmark v1.9 (sección 5: políticas) y Pod Security
    Standards "restricted"
  - ISO/IEC 27001:2022 Anexo A 8.25-8.29 (desarrollo seguro) y
    OWASP SAMM (verificación y despliegue)

Cada política es BLOQUEANTE (detiene el pipeline) o ADVERTENCIA (solo se
informa). Genera reportes en Markdown y JSON y termina con código 1 si
alguna política bloqueante no se cumple.

Uso: python3 scripts/auditoria-cumplimiento.py [--salida reportes/]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
BLOQUEANTE = "BLOQUEANTE"
ADVERTENCIA = "ADVERTENCIA"

resultados = []


def registrar(pid, norma, descripcion, severidad, ok, detalle=""):
    resultados.append({
        "id": pid, "norma": norma, "politica": descripcion, "severidad": severidad,
        "cumple": bool(ok), "detalle": detalle,
    })


def leer(ruta):
    return (RAIZ / ruta).read_text(encoding="utf-8")


# ---------------------------------------------------------------- Dockerfiles
def etapa_final(texto):
    """Devuelve las líneas de la última etapa (desde el último FROM)."""
    lineas = [l.strip() for l in texto.splitlines()]
    inicio = max(i for i, l in enumerate(lineas) if l.upper().startswith("FROM "))
    return lineas[inicio:]


def auditar_dockerfiles():
    for ruta in ["backend/Dockerfile", "frontend/Dockerfile"]:
        texto = leer(ruta)
        final = etapa_final(texto)

        usuarios = [l.split(None, 1)[1] for l in final if l.upper().startswith("USER ")]
        usuario = usuarios[-1] if usuarios else "root (por defecto)"
        registrar(f"DOCKER-01 {ruta}", "CIS Docker 4.1",
                  "El contenedor final corre con un usuario sin privilegios", BLOQUEANTE,
                  usuarios and usuario not in ("root", "0", "0:0"), f"USER final: {usuario}")

        registrar(f"DOCKER-02 {ruta}", "CIS Docker 4.6",
                  "La imagen define un HEALTHCHECK", ADVERTENCIA,
                  any(l.upper().startswith("HEALTHCHECK") for l in final))

        bases = re.findall(r"^FROM\s+(\S+)", texto, flags=re.M | re.I)
        sin_version = [b for b in bases if ":" not in b or b.endswith(":latest")]
        registrar(f"DOCKER-03 {ruta}", "CIS Docker 4.2 / cadena de suministro",
                  "Las imágenes base tienen versión fija (sin :latest)", BLOQUEANTE,
                  not sin_version, ", ".join(sin_version) or ", ".join(bases))

        secreto = re.search(r"^(ENV|ARG)\s+\S*(PASSWORD|SECRET|TOKEN|API_KEY)\S*[ =]\S+", texto,
                            flags=re.M | re.I)
        registrar(f"DOCKER-04 {ruta}", "CIS Docker 4.10",
                  "No hay secretos escritos en ENV/ARG", BLOQUEANTE, secreto is None,
                  secreto.group(0) if secreto else "")


# ----------------------------------------------------------------- Kubernetes
def cargar_manifiestos(carpeta):
    docs = []
    for archivo in sorted((RAIZ / carpeta).glob("*.yaml")):
        if archivo.name == "kustomization.yaml":
            continue
        for doc in yaml.safe_load_all(archivo.read_text(encoding="utf-8")):
            if doc:
                docs.append((archivo.relative_to(RAIZ).as_posix(), doc))
    return docs


def auditar_kubernetes(carpeta="k8s/app"):
    docs = cargar_manifiestos(carpeta)
    workloads = [(a, d) for a, d in docs if d.get("kind") in ("Deployment", "StatefulSet", "DaemonSet")]

    for archivo, d in workloads:
        nombre = f'{d["kind"]}/{d["metadata"]["name"]}'
        pod = d["spec"]["template"]["spec"]
        pod_sc = pod.get("securityContext") or {}
        for c in pod.get("containers", []):
            sc = c.get("securityContext") or {}
            pref = f"{nombre}/{c['name']}"

            no_root = sc.get("runAsNonRoot", pod_sc.get("runAsNonRoot")) is True \
                and sc.get("runAsUser", pod_sc.get("runAsUser", 1)) != 0
            registrar(f"K8S-01 {pref}", "CIS K8s 5.2.6 / PSS restricted",
                      "El contenedor no corre como root", BLOQUEANTE, no_root)

            registrar(f"K8S-02 {pref}", "CIS K8s 5.2.5",
                      "Escalada de privilegios deshabilitada", BLOQUEANTE,
                      sc.get("allowPrivilegeEscalation") is False)

            registrar(f"K8S-03 {pref}", "CIS K8s 5.2.2",
                      "Contenedor no privilegiado", BLOQUEANTE, not sc.get("privileged", False))

            caps = (sc.get("capabilities") or {}).get("drop", [])
            registrar(f"K8S-04 {pref}", "CIS K8s 5.2.8-5.2.9",
                      "Elimina todas las capabilities del kernel", BLOQUEANTE, "ALL" in caps)

            registrar(f"K8S-05 {pref}", "NSA/CISA Kubernetes Hardening",
                      "Sistema de archivos raíz de solo lectura", ADVERTENCIA,
                      sc.get("readOnlyRootFilesystem") is True)

            rec = c.get("resources") or {}
            limites_ok = all(k in (rec.get("limits") or {}) for k in ("cpu", "memory")) \
                and all(k in (rec.get("requests") or {}) for k in ("cpu", "memory"))
            registrar(f"K8S-06 {pref}", "CIS K8s 5.7 / NSA DoS",
                      "Define requests y limits de CPU y memoria", BLOQUEANTE, limites_ok)

            registrar(f"K8S-07 {pref}", "Confiabilidad operacional",
                      "Define livenessProbe y readinessProbe", BLOQUEANTE,
                      "livenessProbe" in c and "readinessProbe" in c)

            imagen = c.get("image", "")
            registrar(f"K8S-08 {pref}", "Cadena de suministro",
                      "La imagen tiene etiqueta y no es :latest", BLOQUEANTE,
                      ":" in imagen and not imagen.endswith(":latest"), imagen)

        registrar(f"K8S-09 {nombre}", "CIS K8s 5.2.4",
                  "No usa la red, PID ni IPC del nodo", BLOQUEANTE,
                  not any(pod.get(k) for k in ("hostNetwork", "hostPID", "hostIPC")))

        registrar(f"K8S-10 {nombre}", "CIS K8s 5.1.6",
                  "No monta el token de la cuenta de servicio sin necesidad", ADVERTENCIA,
                  pod.get("automountServiceAccountToken") is False)

    namespaces = [d for _, d in docs if d.get("kind") == "Namespace"]
    psa = any((n["metadata"].get("labels") or {}).get("pod-security.kubernetes.io/enforce") == "restricted"
              for n in namespaces)
    registrar("K8S-11 Namespace", "Pod Security Standards",
              "El namespace aplica Pod Security 'restricted'", BLOQUEANTE, psa)

    deny = any(d.get("kind") == "NetworkPolicy" and d["spec"].get("podSelector") == {}
               and "Ingress" in d["spec"].get("policyTypes", []) for _, d in docs)
    registrar("K8S-12 NetworkPolicy", "CIS K8s 5.3.2",
              "Existe una NetworkPolicy que deniega todo por defecto", BLOQUEANTE, deny)


# -------------------------------------------------------------- CI/CD y repo
def auditar_pipeline():
    pom = leer("backend/pom.xml")
    m = re.search(r"<counter>LINE</counter>\s*<value>COVEREDRATIO</value>\s*<minimum>([\d.]+)</minimum>", pom)
    registrar("CICD-01", "ISO 27001 A.8.29 / política de calidad",
              "JaCoCo exige al menos 80 % de cobertura", BLOQUEANTE,
              m is not None and float(m.group(1)) >= 0.80, f"mínimo: {m.group(1) if m else 'no definido'}")

    wf_texto = leer(".github/workflows/ci-cd.yml")
    wf = yaml.safe_load(wf_texto)
    jobs = wf.get("jobs", {})

    registrar("CICD-02", "OWASP SAMM - Verificación",
              "El pipeline ejecuta Snyk, SonarQube (Quality Gate), Trivy y esta auditoría", BLOQUEANTE,
              all(s in wf_texto for s in ("snyk test", "sonar.qualitygate.wait=true", "aquasec/trivy",
                                          "auditoria-cumplimiento.py")))

    deploy = jobs.get("deploy", {})
    needs = deploy.get("needs", [])
    needs = [needs] if isinstance(needs, str) else needs
    registrar("CICD-03", "ISO 27001 A.8.32 - Gestión de cambios",
              "El despliegue a producción depende de las validaciones y solo corre en main", BLOQUEANTE,
              bool(needs) and "refs/heads/main" in str(deploy.get("if", "")), f"needs: {needs}")

    usos = re.findall(r"uses:\s*([^\s#]+)", wf_texto)
    flotantes = [u for u in usos if u.endswith(("@main", "@master", "@latest")) or "@" not in u]
    registrar("CICD-04", "Cadena de suministro",
              "Las actions de GitHub tienen versión fija", BLOQUEANTE, not flotantes, ", ".join(flotantes))

    registrar("CICD-05", "ISO 27001 A.8.8 - Vulnerabilidades técnicas",
              "Dependabot está configurado", ADVERTENCIA, (RAIZ / ".github/dependabot.yml").exists())

    registrar("CICD-06", "ISO 27001 A.5.15 - Control de acceso / revisión",
              "Existe CODEOWNERS para exigir revisión de cambios", ADVERTENCIA,
              (RAIZ / ".github/CODEOWNERS").exists())

    registrar("CICD-07", "ISO 27001 A.8.32 - Gestión de cambios",
              "La política de protección de la rama main está versionada", ADVERTENCIA,
              (RAIZ / "politicas/branch-protection.json").exists())


def auditar_secretos_y_compose():
    try:
        versionados = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True,
                                     check=True).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        versionados = []
    prohibidos = [f for f in versionados if re.search(r"(^|/)\.env$|\.pem$|\.key$|id_rsa", f)]
    registrar("SEC-01", "ISO 27001 A.8.12 / CIS Docker 4.10",
              "No hay archivos de credenciales en el repositorio (.env, .pem, .key)", BLOQUEANTE,
              not prohibidos, ", ".join(prohibidos))

    compose = yaml.safe_load(leer("docker-compose.yml"))
    backend = compose["services"]["backend"]
    endurecido = backend.get("read_only") is True and "no-new-privileges:true" in backend.get("security_opt", []) \
        and "ALL" in backend.get("cap_drop", [])
    registrar("COMPOSE-01", "CIS Docker 5.12 / 5.25 / 5.3",
              "Backend en Compose: solo lectura, sin nuevos privilegios ni capabilities", BLOQUEANTE, endurecido)
    registrar("COMPOSE-02", "Mínima exposición",
              "El backend no publica puertos hacia el host", BLOQUEANTE, "ports" not in backend)

    texto_obs = leer("observabilidad/docker-compose.observabilidad.yml")
    clave = re.search(r"(PASSWORD|SECRET)[A-Z_]*:\s*\S+", texto_obs)
    registrar("COMPOSE-03", "ISO 27001 A.5.17 - Información de autenticación",
              "El stack de monitoreo no trae claves por defecto", BLOQUEANTE, clave is None,
              clave.group(0) if clave else "")


# ---------------------------------------------------------------- reportes
def escribir_reportes(salida):
    salida.mkdir(parents=True, exist_ok=True)
    fallas_b = [r for r in resultados if not r["cumple"] and r["severidad"] == BLOQUEANTE]
    fallas_a = [r for r in resultados if not r["cumple"] and r["severidad"] == ADVERTENCIA]
    total = len(resultados)
    cumplen = sum(r["cumple"] for r in resultados)

    (salida / "cumplimiento.json").write_text(json.dumps({
        "total": total, "cumplen": cumplen, "fallas_bloqueantes": len(fallas_b),
        "advertencias": len(fallas_a), "resultados": resultados}, ensure_ascii=False, indent=2), encoding="utf-8")

    lineas = [
        "## Auditoría de cumplimiento",
        "",
        f"**{cumplen} de {total} controles cumplen** · fallas bloqueantes: **{len(fallas_b)}** · "
        f"advertencias: {len(fallas_a)}",
        "",
        "| Resultado | Control | Norma | Política | Detalle |",
        "|---|---|---|---|---|",
    ]
    orden = sorted(resultados, key=lambda r: (r["cumple"], r["severidad"] != BLOQUEANTE, r["id"]))
    for r in orden:
        icono = "✅" if r["cumple"] else ("❌" if r["severidad"] == BLOQUEANTE else "⚠️")
        lineas.append(f"| {icono} | `{r['id']}` | {r['norma']} | {r['politica']} | {r['detalle']} |")
    (salida / "cumplimiento.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return fallas_b


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--salida", default="reportes", help="carpeta para los reportes")
    args = parser.parse_args()

    auditar_dockerfiles()
    auditar_kubernetes()
    auditar_pipeline()
    auditar_secretos_y_compose()

    fallas = escribir_reportes(Path(args.salida))
    for r in resultados:
        if not r["cumple"]:
            print(f"[{r['severidad']}] {r['id']}: {r['politica']} {r['detalle']}".rstrip())
    print(f"{sum(r['cumple'] for r in resultados)}/{len(resultados)} controles cumplen.")
    if fallas:
        print(f"AUDITORÍA BLOQUEADA: {len(fallas)} política(s) bloqueante(s) no se cumplen.")
        return 1
    print("Auditoría aprobada: todas las políticas bloqueantes se cumplen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
