from Agent import agent


class AgentService:
    def ask(self, question: str):
        """Returns (answer, tools_used, success)."""
        return agent.ask(question)


agent_service = AgentService()
