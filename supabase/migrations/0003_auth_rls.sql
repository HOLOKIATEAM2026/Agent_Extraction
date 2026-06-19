-- Ajouter la colonne user_id
ALTER TABLE public.documents ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
ALTER TABLE public.extractions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
ALTER TABLE public.multi_history ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
ALTER TABLE public.chat_history ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
ALTER TABLE public.custom_questions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Activer RLS
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.custom_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.multi_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;

-- Nettoyer les anciennes politiques permissives
DROP POLICY IF EXISTS "Enable read access for all users" ON public.documents;
DROP POLICY IF EXISTS "Enable insert for all users" ON public.documents;
DROP POLICY IF EXISTS "Enable update for all users" ON public.documents;

DROP POLICY IF EXISTS "Enable read access for all users" ON public.extractions;
DROP POLICY IF EXISTS "Enable insert for all users" ON public.extractions;
DROP POLICY IF EXISTS "Enable update for all users" ON public.extractions;

DROP POLICY IF EXISTS "Enable all operations for all users" ON public.multi_history;
DROP POLICY IF EXISTS "Enable all operations for all users" ON public.chat_history;

DROP POLICY IF EXISTS "Enable all access for all users" ON public.custom_questions;
DROP POLICY IF EXISTS "Enable read for all" ON public.custom_questions;
DROP POLICY IF EXISTS "Enable insert for all" ON public.custom_questions;
DROP POLICY IF EXISTS "Enable update for all" ON public.custom_questions;
DROP POLICY IF EXISTS "Enable delete for all" ON public.custom_questions;

-- DOCUMENTS
CREATE POLICY "documents_select" ON public.documents FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY "documents_insert" ON public.documents FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "documents_update" ON public.documents FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "documents_delete" ON public.documents FOR DELETE USING (auth.uid() = user_id);

-- EXTRACTIONS
CREATE POLICY "extractions_select" ON public.extractions FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY "extractions_insert" ON public.extractions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "extractions_update" ON public.extractions FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "extractions_delete" ON public.extractions FOR DELETE USING (auth.uid() = user_id);

-- MULTI_HISTORY
CREATE POLICY "multi_history_select" ON public.multi_history FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY "multi_history_insert" ON public.multi_history FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "multi_history_update" ON public.multi_history FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "multi_history_delete" ON public.multi_history FOR DELETE USING (auth.uid() = user_id);

-- CHAT_HISTORY
CREATE POLICY "chat_history_select" ON public.chat_history FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY "chat_history_insert" ON public.chat_history FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "chat_history_update" ON public.chat_history FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "chat_history_delete" ON public.chat_history FOR DELETE USING (auth.uid() = user_id);

-- CUSTOM_QUESTIONS
CREATE POLICY "custom_questions_select" ON public.custom_questions FOR SELECT USING (auth.uid() = user_id OR is_default = true);
CREATE POLICY "custom_questions_insert" ON public.custom_questions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "custom_questions_update" ON public.custom_questions FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "custom_questions_delete" ON public.custom_questions FOR DELETE USING (auth.uid() = user_id);
