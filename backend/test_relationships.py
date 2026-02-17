import asyncio
from agents.agent import Agent

async def main():
    # Создадим двух агентов
    agent1 = Agent(agent_id=1, name="Маша", personality="добрая")
    agent2 = Agent(agent_id=2, name="Алиса", personality="весёлая")

    # Агент 1 получает сообщение от агента 2 (хорошее)
    agent1.perceive(
        event_text="Алиса сказала: 'Привет, Маша! Ты сегодня отлично выглядишь!'",
        event_delta=+10,  # настроение улучшилось
        other_agent_id=2
    )

    # Проверим отношения агента 1 к агенту 2
    print("Отношения Маши к Алисе:", agent1.relationships.get_affinity(2))

    # Агент 1 получает грубое сообщение
    agent1.perceive(
        event_text="Алиса сказала: 'Отстань, ты мне надоела!'",
        event_delta=-20,
        other_agent_id=2
    )

    print("Отношения Маши к Алисе после грубости:", agent1.relationships.get_affinity(2))

    # Теперь попросим агента 1 принять решение
    action = await agent1.act(other_agents_names=["Алиса", "Боб"])
    print("Действие Маши:", action)

if __name__ == "__main__":
    asyncio.run(main())