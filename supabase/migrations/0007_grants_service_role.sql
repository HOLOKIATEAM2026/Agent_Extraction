GRANT USAGE ON SCHEMA public TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.documents TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.extractions TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.custom_questions TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.multi_history TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.chat_history TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.entreprise_profil TO service_role;

