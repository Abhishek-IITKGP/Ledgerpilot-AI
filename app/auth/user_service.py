from app.auth.user_repository import CreatedUser, UserRepository


class UserService:
    def __init__(self, repository: UserRepository, connection):
        self.repository = repository
        self.connection = connection

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str,
    ) -> CreatedUser:
        try:
            user = self.repository.create_user(
                username=username,
                email=email,
                password=password,
                role=role,
            )
            self.connection.commit()
            return user
        except Exception:
            self.connection.rollback()
            raise
