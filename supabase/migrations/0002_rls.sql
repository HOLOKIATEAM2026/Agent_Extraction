-- Autoriser service_role à bypasser RLS ou définir des politiques explicites
GRANT ALL ON public.documents TO service_role;
GRANT ALL ON public.extractions TO service_role;

-- Créer des politiques pour permettre à tout le monde de lire/écrire (pour la phase de dev)
-- ou au moins au service_role

CREATE POLICY "Enable read access for all users" ON "public"."documents"
AS PERMISSIVE FOR SELECT
TO public
USING (true);

CREATE POLICY "Enable insert for all users" ON "public"."documents"
AS PERMISSIVE FOR INSERT
TO public
WITH CHECK (true);

CREATE POLICY "Enable update for all users" ON "public"."documents"
AS PERMISSIVE FOR UPDATE
TO public
USING (true)
WITH CHECK (true);


CREATE POLICY "Enable read access for all users" ON "public"."extractions"
AS PERMISSIVE FOR SELECT
TO public
USING (true);

CREATE POLICY "Enable insert for all users" ON "public"."extractions"
AS PERMISSIVE FOR INSERT
TO public
WITH CHECK (true);

CREATE POLICY "Enable update for all users" ON "public"."extractions"
AS PERMISSIVE FOR UPDATE
TO public
USING (true)
WITH CHECK (true);