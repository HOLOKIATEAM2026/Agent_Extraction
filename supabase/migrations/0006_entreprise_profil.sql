CREATE TABLE IF NOT EXISTS public.entreprise_profil (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  nom TEXT NOT NULL,
  secteur TEXT,
  score_nist_moyen FLOAT DEFAULT 0,
  score_data_moyen FLOAT DEFAULT 0,
  nb_rapports_analyses INT DEFAULT 0,
  premier_diagnostic DATE,
  dernier_diagnostic DATE,
  points_forts TEXT[],
  axes_amelioration TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS entreprise_profil_user_id_nom_key
ON public.entreprise_profil (user_id, nom);

ALTER TABLE public.entreprise_profil ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS entreprise_profil_select ON public.entreprise_profil;
DROP POLICY IF EXISTS entreprise_profil_insert ON public.entreprise_profil;
DROP POLICY IF EXISTS entreprise_profil_update ON public.entreprise_profil;
DROP POLICY IF EXISTS entreprise_profil_delete ON public.entreprise_profil;

CREATE POLICY entreprise_profil_select ON public.entreprise_profil FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY entreprise_profil_insert ON public.entreprise_profil FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY entreprise_profil_update ON public.entreprise_profil FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY entreprise_profil_delete ON public.entreprise_profil FOR DELETE USING (auth.uid() = user_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON public.entreprise_profil TO authenticated;
