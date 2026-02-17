import asyncio
from agents.agent import Agent

async def run_simulation():
    # Создаём агентов с разными личностями
    agents = [
        Agent(agent_id=1, name="Маша", personality="добрая, отзывчивая, любит помогать", initial_mood=30),
        Agent(agent_id=2, name="Алиса", personality="весёлая, энергичная, иногда болтливая", initial_mood=20),
        Agent(agent_id=3, name="Боб", personality="ворчливый, скептичный, но в душе добряк", initial_mood=-10),
    ]

    # Имена агентов для передачи в act
    agent_names = [a.name for a in agents]

    # Несколько раундов общения
    for round_num in range(5):
        print(f"\n=== Раунд {round_num+1} ===")
        # Каждый агент по очереди совершает действие
        for agent in agents:
            action = await agent.act(agent_names)
            print(f"{agent.name} (настроение: {agent.emotions.get_mood_label()}): {action}")

            # Если действие — сообщение, отправляем его целевому агенту
            if action["type"] == "message":
                target_name = action["target"]
                # Ищем агента по имени
                target = next((a for a in agents if a.name == target_name), None)
                if target:
                    # Сообщение воспринимается целевым агентом
                    # delta настроения: если сообщение дружелюбное или грубое — можно определять по тону,
                    # но для теста будем считать, что любое сообщение от другого агента влияет на настроение
                    # и отношения. В реальности бэкенд может анализировать тональность.
                    # Мы же для простоты будем передавать фиксированную дельту, например +5 за любое сообщение.
                    # Но чтобы было интереснее, будем генерировать дельту случайно или по ключевым словам.
                    # Для теста поставим +2 за сообщение (нейтральное).
                    await target.perceive(
                        event_text=f"{agent.name} сказал: {action['content']}",
                        event_delta=2,
                        other_agent_id=agent.id
                    )
                    print(f"   → {target.name} получил сообщение от {agent.name}")
                else:
                    print(f"   ! Агент с именем {target_name} не найден")

        # Небольшая пауза между раундами для читаемости
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_simulation())