import json, ast
import requests
from datetime import datetime, timezone
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, create_react_agent, AgentExecutor, AgentType
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
from langchain_community.tools.json.tool import JsonSpec
from langchain_community.agent_toolkits.json.toolkit import JsonToolkit
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import os
from os_envs import *
from openai import OpenAI
from RealtimeTTS import TextToAudioStream, SystemEngine
from RealtimeSTT import AudioToTextRecorder
from HuggingFaceTTSEngine import RussianTTSEngine, AutoSystemEngine
import asyncio

from audio import hello_def, goodbye_def
from calendar_tools import Calendar
from prompts import get_prompt


calendar_instance = Calendar()
llm = ChatOpenAI(api_key=os.environ['OPENAI_API_KEY'], temperature=0.7, model_name='gpt-4o-mini')

@tool
def get_current_time() -> str:
    """Provides the current time, date, mounth and year."""
    return datetime.now(timezone.utc).astimezone().isoformat()

# @tool
# def get_weather():
#     pass


# @tool
# def read_mail():
#     pass

# @tool
# def open_link():
#     pass


@tool
def search_internet(query) -> str:
    """Searches the web for relevant information to the user's response and returns up to three relevant links."""
    api_key = os.environ.get('GOOGLE_CUSTOM_SEARCH_API_KEY')
    search_engine_id = os.environ.get('GOOGLE_SEARCH_ENGINE_ID')
    if not api_key or not search_engine_id:
        return "Internet search is unavailable due to missing API keys."
    url = f'https://customsearch.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}+Paphos'

    try:
        response = requests.get(url)
        response.raise_for_status()
        search_results = response.json()
        results = [{
            'title': item['title'],
            'link': item['link']
        } for item in search_results.get('items', [])[:3]]

        formatted_response = "Here are some helpful links:\n"
        for result in results:
            formatted_response += f'- {result["title"]}: {result["link"]}\n'
        return formatted_response
    except Exception as e:
        print(f'Error in Google Search: {e}')
        return "I'm sorry, but I couldn't perform the internet search at the moment. Please try again later."

@tool
def add_google_calendar_event_tool(context_variables):
    """Создает запись в гугл календаре. 
На вход подается dict с ключами: summary, description, dateTime_start, dateTime_end. Так чтобы его можно было распарсить через ast.literal_eval.
где summary - название мероприятия, description - описание мероприятия и все комментарии относительно него, dateTime_start и dateTime_end - дата и время начала и конца в isoformat.
если нет даты, то используй сегодняшнюю дату,
если нет времени, то начала используй время в данный момент,
если нет времени, то окончания используй время в данный момент + 1 час."""  
    return calendar_instance.add_google_calendar_event(ast.literal_eval(context_variables))

tools = [get_current_time, search_internet, add_google_calendar_event_tool, ]
prompt = ChatPromptTemplate.from_template(get_prompt())
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)



async def generate_response_with_stream(agent_executor, input_data):
    """
    Generate assistant's response using LangChain Agent Executor and stream final output token by token.
    """
    final_output = None
    try:
        async for chunk in agent_executor.astream(input_data):
            # Если это финальный вывод (output), стримим токены
            if "output" in chunk:
                final_output = chunk["output"]
                for token in final_output:
                    yield token  # Стриминг финального ответа токенами
            # Логируем промежуточные шаги (опционально)
            elif "actions" in chunk:
                for action in chunk["actions"]:
                    print(f"Calling Tool: `{action.tool}` with input `{action.tool_input}`")
            elif "steps" in chunk:
                for step in chunk["steps"]:
                    print(f"Tool Result: `{step.observation}`")
    except Exception as e:
        print(f"Error during agent execution: {e}")
    finally:
        if not final_output:
            yield "Ошибка: не удалось получить финальный вывод."

def format_history(history):
    """Форматирует историю сообщений в текст для LangChain."""
    formatted = []
    for msg in history:
        if msg["role"] == "user":
            formatted.append(f"Пользователь: {msg['content']}")
        elif msg["role"] == "assistant":
            formatted.append(f"Ассистент: {msg['content']}")
    return "\n".join(formatted)

def update_history(history, role, content):
    """Обновляет историю сообщений."""
    history.append({"role": role, "content": content})

def async_generator_to_iterator(async_gen):
    """Конвертирует асинхронный генератор в синхронный итератор."""
    loop = asyncio.new_event_loop()  # Создаем новый цикл событий
    asyncio.set_event_loop(loop)  # Устанавливаем его как текущий
    try:
        while True:
            try:
                yield loop.run_until_complete(async_gen.__anext__())
            except StopAsyncIteration:
                break
    finally:
        loop.close()  # Закрываем цикл после завершения



if __name__ == '__main__':
    stream = TextToAudioStream(
        # Alternatives: SystemEngine or ElevenlabsEngine
        AutoSystemEngine(),#SystemEngine('Irina'),#RussianTTSEngine(speaker='xenia'),#SystemEngine(), #RussianTTSEngine(speaker='xenia'),
        log_characters=False,#True,
    )

    # Speech-to-Text Recorder Setup
    recorder = AudioToTextRecorder(
        model="large-v2",
        wake_words="bumblebee",
        spinner=True,
        wake_word_activation_delay=5,
        on_wakeword_detection_start=goodbye_def,
        on_wakeword_detection_end=hello_def,
        device="cuda"
    )

    history = []

    def main():
        stream.feed(['Привет!']).play()
        while True:
            user_text = recorder.text().strip()
            if not user_text:
                continue

            print(f">>> {user_text}\n<<< ", end="", flush=True)
            #stream.feed(['Услышал вас, пожалуйста подождите']).play()
            
            
            update_history(history, "user", user_text)
            #chat_history = format_history(history[-10:])
            assistant_response = generate_response_with_stream(agent_executor, 
                {"input": user_text, "chat_history": history[-10:]}
            )
            
            stream.feed(async_generator_to_iterator(assistant_response)).play()
            
            #stream.feed(assistant_response).play()
            update_history(history, "assistant", stream.text())
            
    main()
