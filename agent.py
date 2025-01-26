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

from context_db_tools import ContextDB

context_db = ContextDB()
calendar_instance = Calendar()
llm = ChatOpenAI(api_key=os.environ['OPENAI_API_KEY'], temperature=0.7, model_name='chatgpt-4o-latest')

@tool
def get_current_time() -> str:
    """Provides the current time, date, mounth and year."""
    return datetime.now(timezone.utc).astimezone().isoformat()

# @tool
# def read_mail():
#     pass


import webbrowser
@tool
def open_link(link):
    """
    Открывает ссылку в браузере.
    Вход: link - строка с URL для открытия.
    """
    if link:
        webbrowser.open(link)
        return f"Ссылка {link} успешно открыта в браузере."
    else:
        return "Предоставленная ссылка не является ссылкой"

@tool
def get_weather(city):
    """Finds weather forecast for the specified city. Use only if you know the city!
The city can be viewed in context table, if there is no city in context table, ask the user and then be sure to write it down in the context table.
Input: the 'city' name must be only in English."""
    return get_weather_forecast(city)


@tool
def search_internet(query):
    """Searches the web for relevant information to the user's response and returns up to three relevant links.
Right after that open up one or several links in the browser!"""
    api_key = os.environ.get('GOOGLE_CUSTOM_SEARCH_API_KEY')
    search_engine_id = os.environ.get('GOOGLE_SEARCH_ENGINE_ID')
    if not api_key or not search_engine_id:
        return "Internet search is unavailable due to missing API keys."
    url = f'https://customsearch.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        search_results = response.json()
        results = [{
            'title': item['title'],
            'link': item['link']
        } for item in search_results.get('items', [])[:3]]

        formatted_response = ''
        for result in results:
            formatted_response += f'{result["title"]}: {result["link"]}\n'
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

@tool
def get_events_google_calendar_tool():
    """Возврвщает все записи о будущем в гугл календаре. Вызывай когда нужно понять планы пользователя, а также при составлении рекоменаций"""  
    return calendar_instance.calendar_get_task()

@tool
def delete_event_google_calendar_tool(event_id):
    """Удаляет запись в гугл календаре. На вход передается google calendar id"""  
    return calendar_instance.delete_google_calendar_event(event_id)

@tool
def add_context_tool(context_variables) -> str:
    """
    Добавляет новую запись в контекстную БД.
    На вход подается словарь с ключами:
    - time_of_day (str): Время суток (morning, afternoon, evening, night).
    - description (str): Описание контекста.
    Так чтобы его можно было распарсить через ast.literal_eval.
    Возвращает ID добавленной записи.
    """
    if isinstance(context_variables, str):
        context_variables = ast.literal_eval(context_variables)
    time_of_day = context_variables.get("time_of_day")
    description = context_variables.get("description")
    if not time_of_day or not description:
        return "Ошибка: Укажите time_of_day и description."
    record_id = context_db.add_context(time_of_day, description)
    return f"Запись успешно добавлена с ID {record_id}."

@tool
def get_context_tool(time_of_day) -> list:
    """
    Используется ТОЛЬКО перед удалением строки контекста для получения id определенной записи, либо по запросу пользователя. Не используется в других случаях.
    Возвращает контекст для определенного времени дня.
    На вход подается время суток (morning, afternoon, evening, night).
    """
    if time_of_day == "morning":
        current_hour = 8
    elif time_of_day == "afternoon":
        current_hour = 13
    elif time_of_day == "evening":
        current_hour = 19
    else:
        current_hour = 1
    return context_db.get_context_by_time(current_hour)

@tool
def delete_context_tool(context_id) -> str:
    """
    Удаляет запись из контекстной БД по ID.
    """
    context_id = int(context_id)
    rows_deleted = context_db.delete_context(context_id)
    if rows_deleted > 0:
        return f"Запись с ID {context_id} успешно удалена."
    else:
        return f"Запись с ID {context_id} не найдена."

tools = [
    get_current_time, get_weather,
    search_internet, open_link,
    add_google_calendar_event_tool, get_events_google_calendar_tool,
    add_context_tool, delete_context_tool, get_context_tool,
]
prompt = ChatPromptTemplate.from_template(get_prompt())
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def get_time_of_day():
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        time_of_day = "morning (утро)"
    elif 12 <= current_hour < 17:
        time_of_day = "afternoon (день)"
    elif 17 <= current_hour < 23:
        time_of_day = "evening (вечер)"
    else:
        time_of_day = "night (ночь)"
    return time_of_day

import os
import requests

def get_weather_forecast(city):
    openweather_key = os.environ["WEATHER_API_KEY"]
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={openweather_key}&units=metric'
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return "Ошибка при запросе к API"

    temperature = data['main']['temp']
    cloudiness = data['clouds']['all']
    wind_speed = data['wind']['speed']
    
    return f"Температура: {temperature}°C, скорость ветра: {wind_speed} м/с, облачность: {cloudiness}%."

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
        wake_word_activation_delay=4,
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
            
            user_text = f'{get_time_of_day()} - {datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")}: {user_text}'
            print(f">>> {user_text}\n<<< ", end="", flush=True)
            #stream.feed(['Услышал вас, пожалуйста подождите']).play()
            
            context = context_db.get_context_by_time(datetime.now().hour)
            context = [f'id:{idx}, for {day_time}, {message}\n' for idx,day_time,message in context]
            context = context if context else ["No context for this time"]
            print(context)
            assistant_response = generate_response_with_stream(agent_executor, 
                {"input": user_text, "chat_history": ["Context DB:\n"+' '.join(context)+"\n\nHistory:\n"]+history[-7:]}
                #{"input": user_text, "chat_history": ["History:\n"]+history[-7:]+["\n\nContext DB:\n"+' '.join(context)]}
            )
            
            stream.feed(async_generator_to_iterator(assistant_response)).play()
            
            update_history(history, "user", user_text)
            update_history(history, "assistant", stream.text())
            
    main()
