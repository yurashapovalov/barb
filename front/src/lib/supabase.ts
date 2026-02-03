import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
if (!supabaseUrl) throw new Error("Missing VITE_SUPABASE_URL env var");

const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
if (!supabaseAnonKey) throw new Error("Missing VITE_SUPABASE_ANON_KEY env var");

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
