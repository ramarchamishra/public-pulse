from abc import ABC, abstractmethod

class ScraperInterface(ABC):

    @abstractmethod
    async def load_session(self):
        """Authenticate or restore a session."""
        pass

    @abstractmethod
    async def get_tweets(self,topic:str,limit:int=20):
        pass