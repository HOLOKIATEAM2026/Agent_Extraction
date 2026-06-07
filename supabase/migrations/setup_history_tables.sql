-- Create table for multi-document extraction history
CREATE TABLE IF NOT EXISTS public.multi_history (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    files JSONB NOT NULL DEFAULT '[]'::jsonb,
    questions JSONB NOT NULL DEFAULT '[]'::jsonb,
    model TEXT NOT NULL,
    results JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Set up RLS for multi_history
ALTER TABLE public.multi_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all operations for all users" ON public.multi_history FOR ALL USING (true) WITH CHECK (true);

-- Grant permissions for multi_history
GRANT ALL ON public.multi_history TO anon;
GRANT ALL ON public.multi_history TO authenticated;
GRANT ALL ON public.multi_history TO service_role;

-- Create table for chat history
CREATE TABLE IF NOT EXISTS public.chat_history (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    files JSONB NOT NULL DEFAULT '[]'::jsonb,
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    model TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Set up RLS for chat_history
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all operations for all users" ON public.chat_history FOR ALL USING (true) WITH CHECK (true);

-- Grant permissions for chat_history
GRANT ALL ON public.chat_history TO anon;
GRANT ALL ON public.chat_history TO authenticated;
GRANT ALL ON public.chat_history TO service_role;
