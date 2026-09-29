-- PET Quest: consolidate identity in public.users and remove legacy public.pet_users.
-- Safe behavior: aborts if a legacy row has no matching users.id.
BEGIN;
DO $$
DECLARE orphan_count bigint;
BEGIN
  IF to_regclass('public.pet_users') IS NULL THEN
    RETURN;
  END IF;
  SELECT COUNT(*) INTO orphan_count
  FROM public.pet_users p
  LEFT JOIN public.users u ON u.id=p.local_user_id
  WHERE u.id IS NULL;
  IF orphan_count > 0 THEN
    RAISE EXCEPTION 'Cannot drop pet_users: % orphan row(s) have no matching users.id', orphan_count;
  END IF;
  UPDATE public.users u
  SET username=p.username,
      email=p.email,
      password_hash=p.password_hash,
      name=p.display_name,
      role=p.role,
      profile_mode=p.profile_mode,
      disabled=CASE WHEN p.disabled THEN 1 ELSE 0 END,
      last_login_at=COALESCE(p.last_login_at::text,u.last_login_at)
  FROM public.pet_users p
  WHERE u.id=p.local_user_id;
  DROP TABLE public.pet_users;
END $$;
COMMIT;
