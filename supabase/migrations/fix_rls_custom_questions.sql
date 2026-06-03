ALTER TABLE public.custom_questions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anon read" 
ON public.custom_questions FOR SELECT 
TO anon, authenticated
USING (true);

CREATE POLICY "Allow anon insert" 
ON public.custom_questions FOR INSERT 
TO anon, authenticated
WITH CHECK (true);

CREATE POLICY "Allow anon delete" 
ON public.custom_questions FOR DELETE 
TO anon, authenticated
USING (true);
