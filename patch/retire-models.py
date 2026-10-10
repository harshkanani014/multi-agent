#!/usr/bin/env python3
"""Retire du catalogue prompts/ les modèles qui ne sont plus proposés.

Usage: retire-models.py [--check] [--backup DIR] PROMPTS_DIR

  --check  : rapporte ce qui serait retiré sans rien déplacer (dry-run).
  --backup : répertoire de sauvegarde (obligatoire hors --check).

Un modèle n'est JAMAIS supprimé : il est déplacé dans le répertoire de
sauvegarde de l'upgrade. Un modèle encore référencé par un lien symbolique
de prompts/ (override d'agent, default.model, catalogue .advisor…) est
conservé et signalé MANUAL : le retirer ferait démarrer l'agent, sans erreur
visible, sur le modèle par défaut du CLI. Idempotent : un modèle déjà absent
est ignoré.

Codes retour : 0 = OK (MANUAL compris, non bloquant), 2 = usage.
"""
import os
import shutil
import sys

# Retirés en v3.2.28 (décision opérateur, 2026-10-07).
RETIRED_MODELS = (
    "fable-5.model",
    "gpt-5-3-codex-spark.model",
    "gpt-5-4-mini.model",
    "gpt-5-4.model",
    "gpt-5-5.model",
    "opus-4-5.model",
    "opus-4-6.model",
    "opus-4-7.model",
    "opus-4-8.model",
    "sonnet-4-5.model",
    "sonnet-4-6.model",
)


def symlink_references(prompts_dir):
    """{chemin absolu de la cible: [liens]} pour tous les liens de prompts/."""
    refs = {}
    for root, dirs, files in os.walk(prompts_dir, followlinks=False):
        for name in dirs + files:
            link = os.path.join(root, name)
            if not os.path.islink(link):
                continue
            target = os.path.normpath(os.path.join(root, os.readlink(link)))
            refs.setdefault(target, []).append(os.path.relpath(link, prompts_dir))
    return refs


def retire(prompts_dir, backup_dir, check):
    prompts_dir = os.path.abspath(prompts_dir)
    refs = symlink_references(prompts_dir)
    retired = manual = 0
    for name in RETIRED_MODELS:
        path = os.path.join(prompts_dir, name)
        if not (os.path.lexists(path)):
            continue
        users = sorted(refs.get(path, []))
        if users:
            manual += 1
            print(f"[MANUAL] prompts/{name} conservé : encore référencé par "
                  + ", ".join(users))
            continue
        retired += 1
        if check:
            print(f"[RETIRE] prompts/{name} (déplacé dans la sauvegarde)")
            continue
        os.makedirs(backup_dir, exist_ok=True)
        shutil.move(path, os.path.join(backup_dir, name))
        print(f"[OK]     prompts/{name} → {os.path.join(backup_dir, name)}")
    print(f"retired={retired} manual={manual}")


def main(argv):
    args = list(argv)
    check = "--check" in args
    if check:
        args.remove("--check")
    backup_dir = None
    if "--backup" in args:
        i = args.index("--backup")
        if i + 1 >= len(args):
            print(__doc__, file=sys.stderr)
            return 2
        backup_dir = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1 or not os.path.isdir(args[0]) or (not check and not backup_dir):
        print(__doc__, file=sys.stderr)
        return 2
    retire(args[0], backup_dir, check)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
