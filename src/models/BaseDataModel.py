from sqlalchemy.ext.asyncio import AsyncSession

# parent of every *Model class; holds the session it works with
class BaseDataModel:
    def __init__(self, session: AsyncSession):
        self.session = session