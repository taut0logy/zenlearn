from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from utils.logger import logger


class GeminiService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
        )

    async def generate_response(self, prompt: str) -> str:
        try:
            logger.info(f"Generating response for prompt: {prompt[:50]}...")
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            raise e


gemini_service = GeminiService()
