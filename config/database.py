from supabase import create_client, Client

SUPABASE_URL = "https://iwlscwsenzgyylopnwpu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3bHNjd3NlbnpneXlsb3Bud3B1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIzMDk0MzUsImV4cCI6MjA1Nzg4NTQzNX0.MPF4luLXRsTUCpVTeITSgpMalevZ6pHeP2dtzbdXp_0"
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None
    print(f"⚠️ Supabase indisponível: {e}")
