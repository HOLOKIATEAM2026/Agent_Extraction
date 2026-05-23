create extension if not exists pgcrypto;

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  file_path text not null unique,
  file_name text not null,
  doc_type text not null,
  company text null,
  year int null,
  language text null,
  created_at timestamptz not null default now()
);

create table if not exists public.extractions (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  approach text null,
  provider text null,
  model text null,
  result jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_documents_company_year on public.documents(company, year);
create index if not exists idx_extractions_document_id on public.extractions(document_id);

alter table public.documents enable row level security;
alter table public.extractions enable row level security;
