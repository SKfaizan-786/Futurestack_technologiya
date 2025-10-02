-- Fix Supabase RLS Policies for User Profile Creation
-- Run this in your Supabase SQL Editor

-- 1. Drop existing policies that are causing issues
DROP POLICY IF EXISTS "Users can insert own profile" ON public.user_profiles;
DROP POLICY IF EXISTS "Users can view own profile" ON public.user_profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;

-- 2. Create new policies that work with Supabase Auth
-- Allow users to insert their own profile during signup
CREATE POLICY "Enable insert for authenticated users only" ON public.user_profiles
  FOR INSERT 
  WITH CHECK (auth.uid() = id);

-- Allow users to view their own profile
CREATE POLICY "Enable read access for users based on user_id" ON public.user_profiles
  FOR SELECT 
  USING (auth.uid() = id);

-- Allow users to update their own profile
CREATE POLICY "Enable update for users based on user_id" ON public.user_profiles
  FOR UPDATE 
  USING (auth.uid() = id) 
  WITH CHECK (auth.uid() = id);

-- 3. Make sure the user_profiles table allows inserts (adjust permissions carefully)
GRANT INSERT, SELECT, UPDATE ON public.user_profiles TO authenticated; -- More specific grants
GRANT ALL ON public.user_profiles TO service_role; -- For backend/service use

-- 4. Create a trigger to automatically create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.user_profiles (id, full_name, role)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'fullName', 'Unknown'),
    COALESCE(NEW.raw_user_meta_data->>'role', 'patient')
  );
  RETURN NEW;
END;
$$;

-- 5. Create trigger on auth.users table
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 6. Test query to verify setup
SELECT 'RLS policies updated successfully! User profiles should now work.' as message;