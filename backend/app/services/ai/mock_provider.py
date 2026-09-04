from app.services.ai.base_provider import BaseAIProvider

_MOCK_REPLY = """\
**Observed Data:** Your lab results show Hemoglobin at 11.8 g/dL (reference: 13.0–17.0 g/dL) and Vitamin D at 18 ng/mL (reference: 30–100 ng/mL). Your average sleep is 5.8 hours/night and today's hydration is 51% of your daily target.

**AI Interpretation:** These findings are outside the reference ranges shown on your report. Low hemoglobin and Vitamin D, combined with below-target sleep and hydration, are commonly associated with fatigue — however these observations do not constitute a diagnosis and can have multiple explanations.

**Suggested Action:** Consider discussing your lab results with a qualified healthcare professional who can evaluate your complete medical history. In the meantime, staying consistent with your sleep schedule and increasing water intake throughout the day may support overall wellbeing.

*This response is for educational purposes only. Not a substitute for professional medical advice.*"""


class MockProvider(BaseAIProvider):
    async def chat(self, messages: list[dict], system_prompt: str) -> str:
        return _MOCK_REPLY
