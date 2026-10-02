BEGIN;

INSERT INTO authentication.roles (roleid, "role")
VALUES
    (1, 'ANALYST'),
    (2, 'REVIEWER'),
    (3, 'ADMINISTRATOR')
ON CONFLICT (roleid) DO UPDATE
SET "role" = EXCLUDED."role";

INSERT INTO authentication.permissions (
    permission_id,
    permission_name,
    roleid
)
VALUES
    (1, 'INVESTIGATION_READ', 1),
    (2, 'INVESTIGATION_RUN', 1),
    (3, 'INVESTIGATION_READ', 2),
    (4, 'INVESTIGATION_RUN', 2),
    (5, 'UPDATE_STATUS', 2),
    (6, 'APPROVE_ACTION', 2),
    (7, 'INVESTIGATION_READ', 3),
    (8, 'INVESTIGATION_RUN', 3),
    (9, 'UPDATE_STATUS', 3),
    (10, 'APPROVE_ACTION', 3),
    (11, 'USER_MANAGE', 3)
ON CONFLICT (permission_id) DO UPDATE
SET
    permission_name = EXCLUDED.permission_name,
    roleid = EXCLUDED.roleid;

COMMIT;