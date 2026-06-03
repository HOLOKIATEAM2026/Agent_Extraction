CREATE TABLE IF NOT EXISTS public.custom_questions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    categorie VARCHAR NOT NULL,
    champ VARCHAR NOT NULL,
    question_text TEXT NOT NULL,
    type VARCHAR DEFAULT 'field',
    is_default BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default questions if table is empty
INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'strategique', 'taille_marche', 'Quelle est la taille ou la valeur du marché sur lequel l''entreprise opère ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'taille_marche');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'strategique', 'taux_croissance', 'Quel est le taux de croissance du marché ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'taux_croissance');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'strategique', 'intensite_concurrentielle', 'Comment l''entreprise décrit-elle l''intensité concurrentielle ou la concurrence ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'intensite_concurrentielle');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'strategique', 'concurrents', 'Quels sont les principaux concurrents cités par l''entreprise ?', 'list', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'concurrents');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'strategique', 'tendances_marche', 'Quelles sont les principales tendances du marché ou évolutions sectorielles mentionnées ?', 'list', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'tendances_marche');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'financier', 'chiffre_affaires', 'Quel est le chiffre d''affaires (revenus) total généré par l''entreprise ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'chiffre_affaires');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'financier', 'resultat_net', 'Quel est le résultat net (bénéfice ou perte net) de l''entreprise ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'resultat_net');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'financier', 'ebitda', 'Quel est l''EBITDA (ou EBE - Excédent Brut d''Exploitation) de l''entreprise ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'ebitda');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'rh', 'effectif_total', 'Quel est l''effectif total (nombre d''employés ou de collaborateurs) de l''entreprise ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'effectif_total');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'rh', 'masse_salariale', 'Quelle est la masse salariale (ou frais de personnel) de l''entreprise ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'masse_salariale');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'data', 'existence_donnees', 'Le document mentionne-t-il l''existence de bases de données, d''entrepôts de données (data warehouse) ou de lacs de données (data lake) ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'existence_donnees');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'data', 'qualite', 'Quelles sont les informations sur la qualité des données (nettoyage, standardisation, intégrité) ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'qualite');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'data', 'accessibilite', 'Comment les données sont-elles accessibles ? Y a-t-il des mentions de portails, d''API ou d''outils BI (Business Intelligence) ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'accessibilite');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'data', 'volumetrie', 'Y a-t-il des indications sur la volumétrie (taille en To, Go) des données gérées ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'volumetrie');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'data', 'historisation', 'Le document parle-t-il de l''historisation, de l''archivage ou de la durée de conservation des données ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'historisation');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'data', 'conformite', 'Comment l''entreprise gère-t-il la conformité des données (RGPD, CNIL, protection des données personnelles) ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'conformite');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'data', 'documentation', 'Existe-t-il un dictionnaire de données, un catalogue de données ou une documentation de l''architecture data ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'documentation');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'cyber', 'risques_identifies', 'Quels sont les risques de cybersécurité ou risques informatiques explicitement identifiés ?', 'list', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'risques_identifies');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'cyber', 'conformite_nist', 'Y a-t-il des mentions de conformité à des standards de sécurité comme NIST, ISO 27001 ou autres frameworks cyber ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'conformite_nist');

INSERT INTO public.custom_questions (categorie, champ, question_text, type, is_default)
SELECT 'cyber', 'gouvernance_data', 'Comment s''organise la gouvernance des données (CISO, DPO, comités de sécurité, politiques de sécurité) ?', 'field', true
WHERE NOT EXISTS (SELECT 1 FROM public.custom_questions WHERE champ = 'gouvernance_data');
