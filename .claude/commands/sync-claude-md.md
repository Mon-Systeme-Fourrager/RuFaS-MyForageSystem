# /sync-claude-md

Analyse l'état actuel du dossier courant et de ses sous-dossiers directs.
Compare avec le CLAUDE.md existant à ce niveau (s'il existe).
Identifie :

- Les conventions qui ont changé (nouveaux patterns dans le code)
- Les fichiers/scripts/commandes mentionnés qui n'existent plus
- Les nouvelles dépendances majeures non documentées
- Les sous-dossiers importants sans CLAUDE.md (ex: supabase/functions/, supabase/migrations/)
  Propose un CLAUDE.md mis à jour, en préservant toute section commençant par "## Notes".
  Ne modifie rien sans demander confirmation.
