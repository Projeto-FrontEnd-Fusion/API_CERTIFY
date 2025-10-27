import bcrypt

class HashManager:
    def __init__(self, rounds: int = 12):
        self.rounds = rounds

    def create_hash(self, password: str) -> str:
        if not password:
            raise ValueError("A senha é obrigatória")
        
        salt = bcrypt.gensalt(self.rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify(self, password: str, hashed_password: str) -> bool:
        if not password or not hashed_password:
            raise ValueError("A senha e o hash são obrigatórios para verificação")
        
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
