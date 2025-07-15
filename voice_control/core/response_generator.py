"""Модуль генерации ответов и обратной связи."""

import logging
import random
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
import json
from pathlib import Path

try:
    import openai
except ImportError:
    openai = None

try:
    import requests
except ImportError:
    requests = None

from .command_processor import Command, CommandResult, CommandType


class ResponseType(Enum):
    """Типы ответов."""
    TEXT = "text"
    AUDIO = "audio"
    VISUAL = "visual"
    ACTION = "action"
    NOTIFICATION = "notification"


class ResponseTone(Enum):
    """Тон ответа."""
    FORMAL = "formal"
    FRIENDLY = "friendly"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"


class ResponseLength(Enum):
    """Длина ответа."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    DETAILED = "detailed"


@dataclass
class ResponseContext:
    """Контекст для генерации ответа."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    language: str = "ru"
    tone: ResponseTone = ResponseTone.FRIENDLY
    length: ResponseLength = ResponseLength.MEDIUM
    include_suggestions: bool = True
    personalized: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """Представление ответа."""
    id: str
    text: str
    response_type: ResponseType
    context: ResponseContext
    suggestions: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    generation_time: float = 0.0


class BaseResponseGenerator(ABC):
    """Базовый класс для генераторов ответов."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")
    
    @abstractmethod
    def generate(self, command: Command, context: ResponseContext) -> Response:
        """Генерация ответа на команду."""
        pass
    
    def can_handle(self, command: Command) -> bool:
        """Проверка возможности обработки команды."""
        return True


class TemplateResponseGenerator(BaseResponseGenerator):
    """Генератор ответов на основе шаблонов."""
    
    def __init__(self):
        super().__init__("template")
        self._templates: Dict[str, Dict[str, List[str]]] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Загрузка шаблонов по умолчанию."""
        self._templates = {
            "success": {
                "ru": [
                    "Команда выполнена успешно!",
                    "Готово!",
                    "Выполнено!",
                    "Задача завершена!",
                    "Сделано!",
                    "Команда обработана!"
                ],
                "en": [
                    "Command executed successfully!",
                    "Done!",
                    "Completed!",
                    "Task finished!",
                    "Success!"
                ]
            },
            "error": {
                "ru": [
                    "Произошла ошибка при выполнении команды.",
                    "Не удалось выполнить команду.",
                    "Ошибка выполнения.",
                    "Команда не может быть выполнена.",
                    "Возникла проблема."
                ],
                "en": [
                    "An error occurred while executing the command.",
                    "Failed to execute command.",
                    "Execution error.",
                    "Command cannot be executed."
                ]
            },
            "unknown_command": {
                "ru": [
                    "Команда не распознана. Попробуйте сказать 'помощь' для получения списка команд.",
                    "Я не понимаю эту команду. Скажите 'справка' для помощи.",
                    "Неизвестная команда. Используйте 'помощь' для получения информации.",
                    "Не могу распознать команду. Попробуйте 'помощь'."
                ],
                "en": [
                    "Command not recognized. Try saying 'help' for a list of commands.",
                    "I don't understand this command. Say 'help' for assistance.",
                    "Unknown command. Use 'help' for information."
                ]
            },
            "system_status": {
                "ru": [
                    "Система работает нормально.",
                    "Все системы функционируют корректно.",
                    "Статус: в порядке.",
                    "Система готова к работе."
                ],
                "en": [
                    "System is operating normally.",
                    "All systems are functioning correctly.",
                    "Status: OK.",
                    "System ready."
                ]
            },
            "help": {
                "ru": [
                    "Доступные команды: помощь, статус, открыть, назад, выход.",
                    "Я могу помочь с навигацией и системными командами.",
                    "Основные команды: помощь, статус, навигация, управление."
                ],
                "en": [
                    "Available commands: help, status, open, back, exit.",
                    "I can help with navigation and system commands.",
                    "Main commands: help, status, navigation, control."
                ]
            },
            "greeting": {
                "ru": [
                    "Привет! Как дела?",
                    "Здравствуйте! Чем могу помочь?",
                    "Добро пожаловать!",
                    "Рад вас видеть!"
                ],
                "en": [
                    "Hello! How are you?",
                    "Hi! How can I help?",
                    "Welcome!",
                    "Nice to see you!"
                ]
            },
            "farewell": {
                "ru": [
                    "До свидания!",
                    "Увидимся позже!",
                    "Хорошего дня!",
                    "Пока!"
                ],
                "en": [
                    "Goodbye!",
                    "See you later!",
                    "Have a great day!",
                    "Bye!"
                ]
            }
        }
    
    def generate(self, command: Command, context: ResponseContext) -> Response:
        """Генерация ответа на основе шаблонов."""
        start_time = datetime.now()
        response_id = f"resp_{start_time.timestamp()}_{hash(command.text) % 10000}"
        
        # Определение типа ответа на основе результата команды
        if command.result:
            if command.result.success:
                if "помощь" in command.text.lower() or "справка" in command.text.lower():
                    template_key = "help"
                elif "статус" in command.text.lower():
                    template_key = "system_status"
                elif "привет" in command.text.lower() or "здравствуй" in command.text.lower():
                    template_key = "greeting"
                elif "пока" in command.text.lower() or "до свидания" in command.text.lower():
                    template_key = "farewell"
                else:
                    template_key = "success"
            else:
                template_key = "error"
        else:
            template_key = "unknown_command"
        
        # Получение шаблона
        templates = self._templates.get(template_key, {}).get(context.language, [])
        if not templates:
            templates = self._templates.get(template_key, {}).get("ru", ["Ответ не найден"])
        
        # Выбор случайного шаблона
        base_text = random.choice(templates)
        
        # Персонализация ответа
        response_text = self._personalize_response(base_text, command, context)
        
        # Добавление дополнительной информации
        if command.result and command.result.message:
            if template_key in ["success", "error"]:
                response_text += f" {command.result.message}"
        
        # Генерация предложений
        suggestions = self._generate_suggestions(command, context)
        
        # Генерация действий
        actions = self._generate_actions(command, context)
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        return Response(
            id=response_id,
            text=response_text,
            response_type=ResponseType.TEXT,
            context=context,
            suggestions=suggestions,
            actions=actions,
            metadata={
                "template_key": template_key,
                "generator": self.name,
                "command_id": command.id
            },
            generation_time=generation_time
        )
    
    def _personalize_response(self, text: str, command: Command, context: ResponseContext) -> str:
        """Персонализация ответа."""
        if not context.personalized:
            return text
        
        # Добавление имени пользователя если доступно
        if context.user_id:
            # Здесь можно добавить логику получения имени пользователя
            pass
        
        # Адаптация тона
        if context.tone == ResponseTone.FORMAL:
            text = text.replace("!", ".")
            text = text.replace("Привет", "Здравствуйте")
        elif context.tone == ResponseTone.CASUAL:
            text = text.replace("Здравствуйте", "Привет")
        
        return text
    
    def _generate_suggestions(self, command: Command, context: ResponseContext) -> List[str]:
        """Генерация предложений для пользователя."""
        if not context.include_suggestions:
            return []
        
        suggestions = []
        
        # Предложения на основе типа команды
        if command.command_type == CommandType.SYSTEM:
            if "помощь" in command.text.lower():
                suggestions = ["статус", "открыть файл", "назад"]
            elif "статус" in command.text.lower():
                suggestions = ["помощь", "выход"]
        elif command.command_type == CommandType.NAVIGATION:
            suggestions = ["назад", "вперед", "главная"]
        
        # Ограничение количества предложений
        return suggestions[:3]
    
    def _generate_actions(self, command: Command, context: ResponseContext) -> List[Dict[str, Any]]:
        """Генерация действий для выполнения."""
        actions = []
        
        if command.result and command.result.data:
            data = command.result.data
            if isinstance(data, dict):
                if "action" in data:
                    actions.append({
                        "type": "execute",
                        "action": data["action"],
                        "parameters": data.get("parameters", {})
                    })
        
        return actions
    
    def add_template(self, key: str, language: str, templates: List[str]):
        """Добавление пользовательских шаблонов."""
        if key not in self._templates:
            self._templates[key] = {}
        self._templates[key][language] = templates
    
    def load_templates_from_file(self, file_path: Union[str, Path]):
        """Загрузка шаблонов из файла."""
        with open(file_path, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        for key, lang_templates in templates.items():
            for lang, template_list in lang_templates.items():
                self.add_template(key, lang, template_list)


class AIResponseGenerator(BaseResponseGenerator):
    """Генератор ответов на основе ИИ (OpenAI GPT)."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        super().__init__("ai")
        self.api_key = api_key
        self.model = model
        self._client = None
        
        if openai and api_key:
            try:
                openai.api_key = api_key
                self._client = openai
                self.logger.info("OpenAI клиент инициализирован")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации OpenAI: {e}")
    
    def generate(self, command: Command, context: ResponseContext) -> Response:
        """Генерация ответа с помощью ИИ."""
        start_time = datetime.now()
        response_id = f"ai_resp_{start_time.timestamp()}_{hash(command.text) % 10000}"
        
        if not self._client:
            # Fallback к простому ответу
            return Response(
                id=response_id,
                text="ИИ генератор недоступен",
                response_type=ResponseType.TEXT,
                context=context,
                generation_time=(datetime.now() - start_time).total_seconds()
            )
        
        try:
            # Формирование промпта
            prompt = self._build_prompt(command, context)
            
            # Запрос к OpenAI
            response = self._client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(context)},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self._get_max_tokens(context.length),
                temperature=self._get_temperature(context.tone)
            )
            
            response_text = response.choices[0].message.content.strip()
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return Response(
                id=response_id,
                text=response_text,
                response_type=ResponseType.TEXT,
                context=context,
                metadata={
                    "model": self.model,
                    "generator": self.name,
                    "tokens_used": response.usage.total_tokens,
                    "command_id": command.id
                },
                generation_time=generation_time
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации ИИ ответа: {e}")
            return Response(
                id=response_id,
                text=f"Ошибка генерации ответа: {str(e)}",
                response_type=ResponseType.TEXT,
                context=context,
                generation_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _build_prompt(self, command: Command, context: ResponseContext) -> str:
        """Построение промпта для ИИ."""
        prompt_parts = [
            f"Команда пользователя: {command.text}",
            f"Тип команды: {command.command_type.value}"
        ]
        
        if command.result:
            prompt_parts.append(f"Результат выполнения: {command.result.message}")
            prompt_parts.append(f"Успешно: {'Да' if command.result.success else 'Нет'}")
        
        if command.parameters:
            prompt_parts.append(f"Параметры: {command.parameters}")
        
        prompt_parts.append(f"Сгенерируй ответ на языке: {context.language}")
        prompt_parts.append(f"Тон ответа: {context.tone.value}")
        prompt_parts.append(f"Длина ответа: {context.length.value}")
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self, context: ResponseContext) -> str:
        """Получение системного промпта."""
        if context.language == "ru":
            return (
                "Ты - голосовой ассистент для системы управления. "
                "Отвечай кратко, понятно и дружелюбно. "
                "Помогай пользователю с командами и навигацией."
            )
        else:
            return (
                "You are a voice assistant for a control system. "
                "Respond briefly, clearly and friendly. "
                "Help the user with commands and navigation."
            )
    
    def _get_max_tokens(self, length: ResponseLength) -> int:
        """Получение максимального количества токенов."""
        return {
            ResponseLength.SHORT: 50,
            ResponseLength.MEDIUM: 150,
            ResponseLength.LONG: 300,
            ResponseLength.DETAILED: 500
        }.get(length, 150)
    
    def _get_temperature(self, tone: ResponseTone) -> float:
        """Получение температуры для генерации."""
        return {
            ResponseTone.FORMAL: 0.3,
            ResponseTone.PROFESSIONAL: 0.4,
            ResponseTone.FRIENDLY: 0.7,
            ResponseTone.CASUAL: 0.8,
            ResponseTone.HUMOROUS: 0.9
        }.get(tone, 0.7)


class ResponseGenerator:
    """Главный генератор ответов."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._generators: Dict[str, BaseResponseGenerator] = {}
        self._default_generator = "template"
        self._response_history: List[Response] = []
        self._lock = threading.RLock()
        
        # Регистрация генераторов по умолчанию
        self._register_default_generators()
    
    def _register_default_generators(self):
        """Регистрация генераторов по умолчанию."""
        self.register_generator("template", TemplateResponseGenerator())
    
    def register_generator(self, name: str, generator: BaseResponseGenerator):
        """Регистрация генератора ответов."""
        with self._lock:
            self._generators[name] = generator
            self.logger.info(f"Зарегистрирован генератор: {name}")
    
    def register_ai_generator(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Регистрация ИИ генератора."""
        ai_generator = AIResponseGenerator(api_key, model)
        self.register_generator("ai", ai_generator)
    
    def generate_response(
        self,
        command: Command,
        context: ResponseContext = None,
        generator_name: Optional[str] = None
    ) -> Response:
        """Генерация ответа на команду."""
        if context is None:
            context = ResponseContext()
        
        generator_name = generator_name or self._default_generator
        
        with self._lock:
            generator = self._generators.get(generator_name)
            if not generator:
                self.logger.warning(f"Генератор {generator_name} не найден, используется {self._default_generator}")
                generator = self._generators.get(self._default_generator)
        
        if not generator:
            # Создание простого ответа если генераторы недоступны
            return Response(
                id=f"fallback_{datetime.now().timestamp()}",
                text="Генераторы ответов недоступны",
                response_type=ResponseType.TEXT,
                context=context
            )
        
        try:
            response = generator.generate(command, context)
            
            # Добавление в историю
            with self._lock:
                self._response_history.append(response)
                if len(self._response_history) > 1000:  # Ограничение размера истории
                    self._response_history = self._response_history[-500:]
            
            self.logger.info(f"Ответ сгенерирован: {response.id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации ответа: {e}")
            return Response(
                id=f"error_{datetime.now().timestamp()}",
                text=f"Ошибка генерации ответа: {str(e)}",
                response_type=ResponseType.TEXT,
                context=context
            )
    
    def set_default_generator(self, generator_name: str):
        """Установка генератора по умолчанию."""
        if generator_name in self._generators:
            self._default_generator = generator_name
            self.logger.info(f"Установлен генератор по умолчанию: {generator_name}")
        else:
            self.logger.error(f"Генератор {generator_name} не найден")
    
    def get_response_history(self, limit: int = 100) -> List[Response]:
        """Получение истории ответов."""
        with self._lock:
            return self._response_history[-limit:]
    
    def clear_history(self):
        """Очистка истории ответов."""
        with self._lock:
            self._response_history.clear()
    
    def get_available_generators(self) -> List[str]:
        """Получение списка доступных генераторов."""
        return list(self._generators.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики генерации ответов."""
        with self._lock:
            total_responses = len(self._response_history)
            
            generators_used = {}
            avg_generation_time = 0
            
            for response in self._response_history:
                generator = response.metadata.get("generator", "unknown")
                generators_used[generator] = generators_used.get(generator, 0) + 1
                avg_generation_time += response.generation_time
            
            if total_responses > 0:
                avg_generation_time /= total_responses
            
            return {
                "total_responses": total_responses,
                "generators_used": generators_used,
                "average_generation_time": avg_generation_time,
                "available_generators": len(self._generators),
                "default_generator": self._default_generator
            }


# Функция для создания генератора с настройками по умолчанию
def create_response_generator(ai_api_key: Optional[str] = None) -> ResponseGenerator:
    """Создание генератора ответов с настройками по умолчанию."""
    generator = ResponseGenerator()
    
    if ai_api_key:
        generator.register_ai_generator(ai_api_key)
        generator.set_default_generator("ai")
    
    return generator