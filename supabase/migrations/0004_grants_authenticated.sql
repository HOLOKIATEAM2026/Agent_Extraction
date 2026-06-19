-- Permissions PostgREST (role "authenticated")
-- Sans ces GRANT, Supabase REST renvoie 403 même si les policies RLS existent.

GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.documents TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.extractions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.custom_questions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.multi_history TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.chat_history TO authenticated;

-- (Optionnel) accès lecture seule en mode non connecté
-- GRANT SELECT ON public.custom_questions TO anon;
