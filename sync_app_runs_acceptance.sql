-- Run once in Supabase's SQL Editor to create this function. Called daily via
-- supabase_upload.sync_acceptance_status() (see main.py), right after the
-- pipeline's normal Supabase sync updates besa_projects.
CREATE OR REPLACE FUNCTION sync_app_runs_acceptance()
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
  affected_rows integer;
BEGIN
  UPDATE app_runs ar
  SET acceptance = CASE
    WHEN lower(bp.project_status) IN (
      'ongoing', 'upcoming', 'paid invoice',
      'completed project not paid', 'competed project not paid' -- covers possible typo in stored data
    ) THEN 'accepted'
    WHEN lower(bp.project_status) = 'no response/refusal' THEN 'rejected'
    WHEN lower(bp.project_status) = 'warm lead' THEN 'negotiating'
    ELSE ar.acceptance
  END
  FROM besa_projects bp
  WHERE ar.besa_project_id = bp.project_id
    AND lower(bp.project_status) IN (
      'ongoing', 'upcoming', 'paid invoice',
      'completed project not paid', 'competed project not paid',
      'no response/refusal', 'warm lead'
    );

  GET DIAGNOSTICS affected_rows = ROW_COUNT;
  RETURN affected_rows;
END;
$$;
