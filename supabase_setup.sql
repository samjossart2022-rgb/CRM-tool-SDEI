-- Portfolio CRM: Supabase table setup
-- Run this in Supabase SQL Editor (https://supabase.com/dashboard > SQL Editor)

-- Companies table
create table if not exists companies (
    company_id text primary key,
    company_name text not null,
    contact_name text not null default '',
    contact_email text not null default '',
    portfolio_manager text default '',
    fund text default '',
    reporting_cadence text default 'Monthly',
    next_due_date date,
    access_token text,
    is_active boolean default true,
    created_at timestamptz default now()
);

-- Company updates table
create table if not exists company_updates (
    update_id text primary key,
    submission_date date,
    company_id text references companies(company_id) on delete cascade,
    company_name text,
    reporting_period text,
    revenue text default '',
    expenses text default '',
    cash text default '',
    runway_months integer default 0,
    wins text default '',
    challenges text default '',
    asks text default '',
    investment_update text default '',
    narrative text default '',
    meeting_agenda text default '',
    meeting_minutes text default '',
    data_warehouse_link text default '',
    submitted_by text default '',
    created_at timestamptz default now()
);

-- Row Level Security: allow all operations via anon key
-- (Tighten these policies later if you add authentication)
alter table companies enable row level security;
alter table company_updates enable row level security;

create policy "Allow all on companies" on companies
    for all using (true) with check (true);

create policy "Allow all on company_updates" on company_updates
    for all using (true) with check (true);
