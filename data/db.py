import aiosqlite
import asyncio
import logging

class Database:
    def __init__(self, db_path: str, max_retries: int = 3, retry_delay: float = 1.0):
        self.db_path = db_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conn = None

    async def connect(self):
        for attempt in range(self.max_retries):
            try:
                self.conn = await aiosqlite.connect(self.db_path)
                await self.initialize_schema()
                break
            except Exception as e:
                logging.error(f"Failed to connect to database (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        else:
            raise Exception("Failed to connect to the database after multiple attempts")

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def ensure_connection(self):
        if not self.conn or not self.conn._conn:
            await self.connect()

    async def execute(self, query: str, *args):
        await self.ensure_connection()
        for attempt in range(self.max_retries):
            try:
                async with self.conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    await self.conn.commit()
                    return cursor
            except Exception as e:
                logging.error(f"Failed to execute query (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        else:
            raise Exception("Failed to execute query after multiple attempts")

    async def fetchone(self, query: str, *args):
        await self.ensure_connection()
        for attempt in range(self.max_retries):
            try:
                async with self.conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    return await cursor.fetchone()
            except Exception as e:
                logging.error(f"Failed to fetch one (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        else:
            raise Exception("Failed to fetch one after multiple attempts")
        
    async def fetchall(self, query: str, *args):
        await self.ensure_connection()
        for attempt in range(self.max_retries):
            try:
                async with self.conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    return await cursor.fetchall()
            except Exception as e:
                logging.error(f"Failed to fetch all (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        else:
            raise Exception("Failed to fetch all after multiple attempts")

    async def initialize_schema(self):
        schema = DatabaseSchema()
        for query in schema.create_table_queries:
            await self.execute(query)

class DatabaseSchema:
    def __init__(self):
        self.create_table_queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                bio TEXT,
                vip INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS interactions (
                user_id INTEGER,
                target_id INTEGER,
                interaction TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, target_id)
            )
            """
        ]

class User:
    def __init__(self, user_id: int, bio: str = None, vip: bool = False):
        self.user_id = user_id
        self.bio = bio
        self.vip = vip

    def __repr__(self):
        return f"User(id={self.user_id}, bio={self.bio}, vip={self.vip})"
    
class Like:
    def __init__(self, user_id: int, liked_user_id: int):
        self.user_id = user_id
        self.liked_user_id = liked_user_id

    def __repr__(self):
        return f"Like(user_id={self.user_id}, liked_user_id={self.liked_user_id})"
    
class Match:
    def __init__(self, user1_id: int, user2_id: int):
        self.user1_id = user1_id
        self.user2_id = user2_id

    def __repr__(self):
        return f"Match(user1_id={self.user1_id}, user2_id={self.user2_id})"
    
class Dislike:
    def __init__(self, user_id: int, disliked_user_id: int):
        self.user_id = user_id
        self.disliked_user_id = disliked_user_id

    def __repr__(self):
        return f"Dislike(user_id={self.user_id}, disliked_user_id={self.disliked_user_id})"
