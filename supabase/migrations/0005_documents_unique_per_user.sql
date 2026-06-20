-- Rendre la déduplication des documents multi-tenant
-- Problème: file_path est UNIQUE globalement => un autre user déclenche un upsert (UPDATE) interdit par RLS => 403
-- Solution: UNIQUE (user_id, file_path) + on_conflict sur (user_id,file_path)

ALTER TABLE public.documents DROP CONSTRAINT IF EXISTS documents_file_path_key;
DROP INDEX IF EXISTS public.documents_file_path_key;

CREATE UNIQUE INDEX IF NOT EXISTS documents_user_id_file_path_key
ON public.documents (user_id, file_path);
