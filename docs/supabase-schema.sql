-- Supabase schema for AI Debate Trainer.
-- Run this file in Supabase SQL Editor before using STORAGE_PROVIDER=supabase.

create table if not exists public.profiles (
    id text primary key,
    email text unique,
    display_name text,
    profile_level text default 'intermediate',
    preferred_language text default 'vi',
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.debate_sessions (
    id text primary key,
    user_id text not null references public.profiles(id) on delete cascade,
    topic text not null,
    topic_id text,
    topic_category text,
    stance text,
    ai_stance text,
    difficulty text,
    practice_mode text not null default 'free_debate',
    status text not null default 'active',
    turn_count integer not null default 0,
    average_score numeric not null default 0,
    metadata jsonb not null default '{}'::jsonb,
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.practice_prompts (
    id text primary key,
    session_id text references public.debate_sessions(id) on delete cascade,
    user_id text not null references public.profiles(id) on delete cascade,
    mode text not null,
    topic text,
    topic_id text,
    category text,
    difficulty text,
    prompt_type text,
    prompt_text text,
    instruction text,
    round_number integer not null default 1,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.debate_turns (
    id text primary key,
    session_id text not null references public.debate_sessions(id) on delete cascade,
    user_id text not null references public.profiles(id) on delete cascade,
    practice_prompt_id text references public.practice_prompts(id) on delete set null,
    turn_number integer not null,
    user_argument text not null,
    ai_rebuttal text,
    input_type text not null default 'text',
    practice_mode text,
    is_valid boolean not null default true,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.cer_scores (
    id text primary key,
    turn_id text not null references public.debate_turns(id) on delete cascade,
    session_id text not null references public.debate_sessions(id) on delete cascade,
    user_id text not null references public.profiles(id) on delete cascade,
    claim numeric not null default 0,
    evidence numeric not null default 0,
    reasoning numeric not null default 0,
    overall numeric not null default 0,
    total numeric not null default 0,
    created_at timestamptz not null default now()
);

create table if not exists public.feedback_items (
    id text primary key,
    turn_id text not null references public.debate_turns(id) on delete cascade,
    session_id text not null references public.debate_sessions(id) on delete cascade,
    user_id text not null references public.profiles(id) on delete cascade,
    feedback_type text not null,
    content text not null,
    created_at timestamptz not null default now()
);

create table if not exists public.content_flags (
    id text primary key,
    turn_id text not null references public.debate_turns(id) on delete cascade,
    session_id text not null references public.debate_sessions(id) on delete cascade,
    user_id text not null references public.profiles(id) on delete cascade,
    flag_type text not null default 'ai_error',
    message text not null default '',
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.user_memories (
    user_id text primary key references public.profiles(id) on delete cascade,
    version integer not null default 1,
    memory jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.session_memories (
    session_id text primary key references public.debate_sessions(id) on delete cascade,
    user_id text not null references public.profiles(id) on delete cascade,
    memory jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_debate_sessions_user_created
    on public.debate_sessions(user_id, created_at desc);

create index if not exists idx_debate_turns_session_turn
    on public.debate_turns(session_id, turn_number);

create index if not exists idx_cer_scores_session
    on public.cer_scores(session_id);

create index if not exists idx_feedback_items_turn_created
    on public.feedback_items(turn_id, created_at);

create index if not exists idx_practice_prompts_session_mode_created
    on public.practice_prompts(session_id, mode, created_at);

-- The current backend uses SUPABASE_SERVICE_ROLE_KEY for database writes.
-- Enable RLS now, then keep service-role-only backend access until direct
-- browser Supabase clients are introduced.
alter table public.profiles enable row level security;
alter table public.debate_sessions enable row level security;
alter table public.practice_prompts enable row level security;
alter table public.debate_turns enable row level security;
alter table public.cer_scores enable row level security;
alter table public.feedback_items enable row level security;
alter table public.content_flags enable row level security;
alter table public.user_memories enable row level security;
alter table public.session_memories enable row level security;

-- Optional user-facing read policies. Uncomment only if the frontend starts
-- reading Supabase directly with user access tokens instead of going through
-- the FastAPI backend.
--
-- create policy "profiles_select_own" on public.profiles
--     for select using (auth.uid()::text = id);
-- create policy "debate_sessions_select_own" on public.debate_sessions
--     for select using (auth.uid()::text = user_id);
-- create policy "practice_prompts_select_own" on public.practice_prompts
--     for select using (auth.uid()::text = user_id);
-- create policy "debate_turns_select_own" on public.debate_turns
--     for select using (auth.uid()::text = user_id);
-- create policy "cer_scores_select_own" on public.cer_scores
--     for select using (auth.uid()::text = user_id);
-- create policy "feedback_items_select_own" on public.feedback_items
--     for select using (auth.uid()::text = user_id);
-- create policy "content_flags_select_own" on public.content_flags
--     for select using (auth.uid()::text = user_id);
-- create policy "user_memories_select_own" on public.user_memories
--     for select using (auth.uid()::text = user_id);
-- create policy "session_memories_select_own" on public.session_memories
--     for select using (auth.uid()::text = user_id);
