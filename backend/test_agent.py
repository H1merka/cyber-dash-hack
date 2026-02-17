import asyncio
from agents.agent import Agent

async def main():
    # Создадим агента
    agent = Agent(
        agent_id=1,
        name="Маша",
        personality="добрая, любопытная",
        initial_mood=20  # хорошее
    )
    
    # Добавим несколько воспоминаний
    agent.perceive("Сегодня я встретила подругу.", event_delta=5)
    agent.perceive("Она сказала, что у неё всё отлично.", event_delta=2)
    agent.perceive("Потом пошёл дождь, и я промокла.", event_delta=-10)
    
    # Спросим, что делать
    action = await agent.act(other_agents_names=["Алиса", "Боб"])
    print("Действие агента:", action)

if __name__ == "__main__":
    asyncio.run(main())

# python backend/test_agent.py