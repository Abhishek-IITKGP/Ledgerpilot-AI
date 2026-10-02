from dataclasses import dataclass


@dataclass
class CreatedUser:
    user_id: int
    username: str
    email: str
    role: str
    is_active: bool


@dataclass
class AuthenticatedUser:
    user_id: int
    username: str
    email: str
    is_active: bool
    role: str | None


class UserRepository:
    def __init__(self, connection):
        self.connection = connection

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str,
    ) -> CreatedUser:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT roleid, \"role\" FROM authentication.roles "
                "WHERE UPPER(\"role\") = UPPER(%s)",
                (role,),
            )
            role_row = cursor.fetchone()

            if role_row is None:
                raise ValueError(f"Role {role} does not exist")

            role_id, role_name = role_row

            # The current schema uses an integer userid without a sequence.
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", (814237,))
            cursor.execute(
                """
                SELECT COALESCE(MAX(userid), 0) + 1
                FROM authentication.users
                """
            )
            user_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO authentication.users (
                    userid,
                    username,
                    email,
                    password_hash,
                    is_active
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    crypt(%s, gen_salt('bf', 10)),
                    TRUE
                )
                RETURNING userid, username, email, is_active
                """,
                (user_id, username, email, password),
            )

            user_row = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO authentication.user_role_mappings (userid, roleid)
                VALUES (%s, %s)
                """,
                (user_id, role_id),
            )

        return CreatedUser(
            user_id=user_row[0],
            username=user_row[1],
            email=user_row[2],
            role=role_name,
            is_active=user_row[3],
        )
    def get_by_email(self, email: str):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.userid,
                    u.username,
                    u.email,
                    u.password_hash,
                    u.is_active,
                    r."role"
                FROM authentication.users AS u
                LEFT JOIN authentication.user_role_mappings AS urm
                    ON urm.userid = u.userid
                LEFT JOIN authentication.roles AS r
                    ON r.roleid = urm.roleid
                WHERE LOWER(u.email) = LOWER(%s)
                """,
                (email,),
            )

            return cursor.fetchone()

    def get_by_id(self, user_id: int) -> AuthenticatedUser | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.userid,
                    u.username,
                    u.email,
                    u.is_active,
                    r."role"
                FROM authentication.users AS u
                LEFT JOIN authentication.user_role_mappings AS urm
                    ON urm.userid = u.userid
                LEFT JOIN authentication.roles AS r
                    ON r.roleid = urm.roleid
                WHERE u.userid = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return AuthenticatedUser(
            user_id=row[0],
            username=row[1],
            email=row[2],
            is_active=row[3],
            role=row[4],
        )
        
    def verify_password(
        self,
        email: str,
        password: str,
    ):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.userid,
                    u.username,
                    u.email,
                    u.is_active,
                    r."role",
                    crypt(%s, u.password_hash) = u.password_hash
                        AS password_valid
                FROM authentication.users AS u
                LEFT JOIN authentication.user_role_mappings AS urm
                    ON urm.userid = u.userid
                LEFT JOIN authentication.roles AS r
                    ON r.roleid = urm.roleid
                WHERE LOWER(u.email) = LOWER(%s)
                """,
                (password, email),
            )

            row = cursor.fetchone()

        if row is None or not row[5]:
            return None

        return AuthenticatedUser(
            user_id=row[0],
            username=row[1],
            email=row[2],
            is_active=row[3],
            role=row[4],
        )