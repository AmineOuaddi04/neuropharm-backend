from app.db.supabase import supabase

res = supabase.table("users").select("*").limit(1).execute()
print(res.data)