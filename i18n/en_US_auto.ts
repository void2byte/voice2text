<?xml version='1.0' encoding='utf-8'?>
<TS version="2.1" language="en_US">
<context>
    <name>FileSettingsTab</name>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="33" />
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="172" />
        <source>Именование файлов</source>
        <translation>File Naming</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="38" />
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="176" />
        <source>Добавлять временную метку к имени файла</source>
        <translation>Add timestamp to filename</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="43" />
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="180" />
        <source>Формат временной метки:</source>
        <translation>Timestamp format:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="53" />
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="181" />
        <source>Пример:</source>
        <translation>Example:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="59" />
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="177" />
        <source>Создавать подпапки по дате</source>
        <translation>Create subfolders by date</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="65" />
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="173" />
        <source>Формат изображения</source>
        <translation>Image format</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="71" />
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="185" />
        <source>PNG (без потерь)</source>
        <translation>PNG (lossless)</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="72" />
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="186" />
        <source>JPEG (с сжатием)</source>
        <translation>JPEG (with compression)</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="82" />
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="182" />
        <source>Качество JPEG:</source>
        <translation>JPEG Quality:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/file_settings_tab.py" line="151" />
        <source>Неверный формат!</source>
        <translation>Invalid format!</translation>
    </message>
</context>
<context>
    <name>GoogleSettingsTab</name>
    <message>
        <location filename="../voice_control/ui/settings_tabs/google_settings_tab.py" line="22" />
        <source>Настройки Google Cloud Speech-to-Text</source>
        <translation>Google Cloud Speech-to-Text Settings</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/google_settings_tab.py" line="23" />
        <source>Введите API-ключ Google</source>
        <translation>Enter Google API key</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/google_settings_tab.py" line="29" />
        <source>API-ключ:</source>
        <translation>API key:</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/google_settings_tab.py" line="60" />
        <source>API-ключ Google не введен.</source>
        <translation>Google API key not entered.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/google_settings_tab.py" line="98" />
        <source>Ошибка Google</source>
        <translation>Google Error</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/google_settings_tab.py" line="98" />
        <source>Введите API-ключ для Google Cloud Speech-to-Text.</source>
        <translation>Enter API key for Google Cloud Speech-to-Text.</translation>
    </message>
</context>
<context>
    <name>InfoTab</name>
    <message>
        <location filename="../voice_control/ui/info_tab.py" line="48" />
        <source>О технологиях распознавания</source>
        <translation>About recognition technologies</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/info_tab.py" line="81" />
        <source>
        &lt;h2&gt;Технологии распознавания речи&lt;/h2&gt;
        &lt;p&gt;Это приложение поддерживает несколько движков распознавания речи, включая Yandex SpeechKit, Google Cloud Speech-to-Text и офлайн-распознавание с помощью Vosk.&lt;/p&gt;

        &lt;h3&gt;Yandex SpeechKit&lt;/h3&gt;
        &lt;ul&gt;
            &lt;li&gt;&lt;b&gt;Описание:&lt;/b&gt; Облачный сервис от Яндекса для распознавания и синтеза речи.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Требования:&lt;/b&gt; API-ключ от Яндекс.Облака.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Особенности:&lt;/b&gt; Поддержка нескольких языков, специализированные модели.&lt;/li&gt;
        &lt;/ul&gt;

        &lt;h3&gt;Google Cloud Speech-to-Text&lt;/h3&gt;
        &lt;ul&gt;
            &lt;li&gt;&lt;b&gt;Описание:&lt;/b&gt; Сервис от Google для преобразования речи в текст.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Требования:&lt;/b&gt; JSON-ключ сервисного аккаунта Google Cloud.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Особенности:&lt;/b&gt; Высокая точность, поддержка множества языков и диалектов.&lt;/li&gt;
        &lt;/ul&gt;

        &lt;h3&gt;Vosk&lt;/h3&gt;
        &lt;ul&gt;
            &lt;li&gt;&lt;b&gt;Описание:&lt;/b&gt; Офлайн-библиотека для распознавания речи.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Требования:&lt;/b&gt; Предварительно загруженная модель для нужного языка.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Особенности:&lt;/b&gt; Работает без подключения к интернету, что обеспечивает приватность данных.&lt;/li&gt;
        &lt;/ul&gt;

        &lt;h3&gt;Рекомендации по качеству аудио&lt;/h3&gt;
        &lt;ul&gt;
            &lt;li&gt;Используйте качественный микрофон.&lt;/li&gt;
            &lt;li&gt;Минимизируйте фоновый шум.&lt;/li&gt;
            &lt;li&gt;Говорите четко и не слишком быстро.&lt;/li&gt;
            &lt;li&gt;Для лучшего результата используйте частоту дискретизации 16000 Гц.&lt;/li&gt;
        &lt;/ul&gt;
        </source>
        <translation>&lt;h2&gt;Speech Recognition Technologies&lt;/h2&gt;
        &lt;p&gt;This application supports several speech recognition engines, including Yandex SpeechKit, Google Cloud Speech-to-Text, and offline recognition with Vosk.&lt;/p&gt;

        &lt;h3&gt;Yandex SpeechKit&lt;/h3&gt;
        &lt;ul&gt;
            &lt;li&gt;&lt;b&gt;Description:&lt;/b&gt; A cloud service from Yandex for speech recognition and synthesis.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Requirements:&lt;/b&gt; API key from Yandex.Cloud.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Features:&lt;/b&gt; Support for multiple languages, specialized models.&lt;/li&gt;
        &lt;/ul&gt;

        &lt;h3&gt;Google Cloud Speech-to-Text&lt;/h3&gt;
        &lt;ul&gt;
            &lt;li&gt;&lt;b&gt;Description:&lt;/b&gt; A service from Google for converting speech to text.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Requirements:&lt;/b&gt; JSON key of a Google Cloud service account.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Features:&lt;/b&gt; High accuracy, support for many languages and dialects.&lt;/li&gt;
        &lt;/ul&gt;

        &lt;h3&gt;Vosk&lt;/h3&gt;
        &lt;ul&gt;
            &lt;li&gt;&lt;b&gt;Description:&lt;/b&gt; An offline library for speech recognition.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Requirements:&lt;/b&gt; A pre-trained model for the desired language.&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Features:&lt;/b&gt; Works without an internet connection, which ensures data privacy.&lt;/li&gt;
        &lt;/ul&gt;

        &lt;h3&gt;Audio Quality Recommendations&lt;/h3&gt;
        &lt;ul&gt;
            &lt;li&gt;Use a high-quality microphone.&lt;/li&gt;
            &lt;li&gt;Minimize background noise.&lt;/li&gt;
            &lt;li&gt;Speak clearly and not too fast.&lt;/li&gt;
            &lt;li&gt;For best results, use a sample rate of 16000 Hz.&lt;/li&gt;
        &lt;/ul&gt;</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/info_tab.py" line="82" />
        <source>Открыть документацию</source>
        <translation>Open documentation</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/info_tab.py" line="83" />
        <source>Текущий распознаватель</source>
        <translation>Current recognizer</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/info_tab.py" line="157" />
        <source>Распознаватель не выбран или не инициализирован.</source>
        <translation>Recognizer not selected or initialized.</translation>
    </message>
</context>
<context>
    <name>MagnifierSettingsTab</name>
    <message>
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="38" />
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="125" />
        <source>Настройки лупы</source>
        <translation>Magnifier settings</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="43" />
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="126" />
        <source>Включить лупу</source>
        <translation>Enable magnifier</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="48" />
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="127" />
        <source>Размер лупы (px):</source>
        <translation>Magnifier size (px):</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="59" />
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="128" />
        <source>Коэффициент увеличения:</source>
        <translation>Magnification factor:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="70" />
        <location filename="../settings_modules/tabs/magnifier_settings_tab.py" line="129" />
        <source>Показывать сетку в лупе</source>
        <translation>Show grid in magnifier</translation>
    </message>
</context>
<context>
    <name>MainSettingsTab</name>
    <message>
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="38" />
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="117" />
        <source>Язык</source>
        <translation>Language</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="42" />
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="118" />
        <source>Язык интерфейса:</source>
        <translation>Interface language:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="53" />
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="119" />
        <source>Режим работы</source>
        <translation>Operating mode</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="57" />
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="120" />
        <source>Режим после распознавания:</source>
        <translation>Mode after recognition:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="60" />
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="121" />
        <source>Обычный режим</source>
        <translation>Normal mode</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="61" />
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="122" />
        <source>Копировать и скрыть</source>
        <translation>Copy and hide</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="63" />
        <location filename="../settings_modules/tabs/main_settings_tab.py" line="123" />
        <source>Копировать, очистить и скрыть</source>
        <translation>Copy, clear and hide</translation>
    </message>
</context>
<context>
    <name>MicrophoneControlWidget</name>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="81" />
        <source>Устройство ввода</source>
        <translation>Input device</translation>
    </message>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="86" />
        <source>Микрофон:</source>
        <translation>Microphone:</translation>
    </message>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="90" />
        <source>Обновить</source>
        <translation>Refresh</translation>
    </message>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="97" />
        <source>Управление записью</source>
        <translation>Recording control</translation>
    </message>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="102" />
        <source>Громкость:</source>
        <translation>Volume:</translation>
    </message>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="114" />
        <source>Время записи:</source>
        <translation>Recording time:</translation>
    </message>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="116" />
        <source>00:00.0</source>
        <translation>00:00.0</translation>
    </message>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="125" />
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="221" />
        <source>Начать запись</source>
        <translation>Start Recording</translation>
    </message>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="129" />
        <source>Сохранить запись</source>
        <translation>Save Recording</translation>
    </message>
    <message>
        <location filename="../voice_control/microphone/qt_mic_gui.py" line="202" />
        <source>Остановить запись</source>
        <translation>Stop Recording</translation>
    </message>
</context>
<context>
    <name>NotificationSettingsTab</name>
    <message>
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="31" />
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="99" />
        <source>Показывать уведомления</source>
        <translation>Show notifications</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="36" />
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="103" />
        <source>При запуске приложения</source>
        <translation>On application startup</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="40" />
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="104" />
        <source>При захвате экрана</source>
        <translation>On screen capture</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="44" />
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="105" />
        <source>При сохранении файла</source>
        <translation>On file save</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="50" />
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="100" />
        <source>Звуковые эффекты</source>
        <translation>Sound effects</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="55" />
        <location filename="../settings_modules/tabs/notification_settings_tab.py" line="106" />
        <source>Включить звуковые уведомления</source>
        <translation>Enable sound notifications</translation>
    </message>
</context>
<context>
    <name>RecognitionTab</name>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="181" />
        <source>Сначала настройте API-ключ и параметры распознавания</source>
        <translation>First, configure API key and recognition parameters</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="285" />
        <source>Нет результатов для сохранения</source>
        <translation>No results to save</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="181" />
        <location filename="../voice_control/ui/recognition_tab.py" line="285" />
        <location filename="../voice_control/ui/recognition_tab.py" line="307" />
        <source>Ошибка</source>
        <translation>Error</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="73" />
        <source>Здесь будут отображаться результаты распознавания...</source>
        <translation>Recognition results will be displayed here...</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="75" />
        <source>Сохранить</source>
        <translation>Save</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="294" />
        <source>Сохранить результаты</source>
        <translation>Save results</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="303" />
        <source>Успех</source>
        <translation>Success</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="72" />
        <source>Результаты распознавания</source>
        <translation>Recognition results</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="74" />
        <source>Очистить</source>
        <translation>Clear</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="71" />
        <source>Голосовой ввод</source>
        <translation>Voice input</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/recognition_tab.py" line="295" />
        <source>Текстовые файлы (*.txt)</source>
        <translation>Text files (*.txt)</translation>
    </message>
</context>
<context>
    <name>SelectionSettingsTab</name>
    <message>
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="39" />
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="130" />
        <source>Минимальные размеры выделения</source>
        <translation>Minimum selection sizes</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="45" />
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="134" />
        <source>Минимальная ширина (px):</source>
        <translation>Minimum width (px):</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="56" />
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="135" />
        <source>Минимальная высота (px):</source>
        <translation>Minimum height (px):</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="68" />
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="131" />
        <source>Затемнение фона</source>
        <translation>Background dimming</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="74" />
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="136" />
        <source>Степень затемнения:</source>
        <translation>Dimming level:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="90" />
        <location filename="../settings_modules/tabs/selection_settings_tab.py" line="137" />
        <source>0% - без затемнения, 100% - полностью темный</source>
        <translation>0% - no dimming, 100% - completely dark</translation>
    </message>
</context>
<context>
    <name>SelectorSettingsDialog</name>
    <message>
        <location filename="../settings_modules/selector_settings_dialog.py" line="97" />
        <location filename="../settings_modules/selector_settings_dialog.py" line="279" />
        <source>Выделение</source>
        <translation>Selection</translation>
    </message>
    <message>
        <location filename="../settings_modules/selector_settings_dialog.py" line="238" />
        <source>Настройки были изменены. Сохранить изменения?</source>
        <translation>Settings have been changed. Save changes?</translation>
    </message>
    <message>
        <location filename="../settings_modules/selector_settings_dialog.py" line="237" />
        <source>Сохранение настроек</source>
        <translation>Saving settings</translation>
    </message>
    <message>
        <location filename="../settings_modules/selector_settings_dialog.py" line="115" />
        <location filename="../settings_modules/selector_settings_dialog.py" line="281" />
        <source>Интерфейс</source>
        <translation>Interface</translation>
    </message>
    <message>
        <location filename="../settings_modules/selector_settings_dialog.py" line="142" />
        <location filename="../settings_modules/selector_settings_dialog.py" line="287" />
        <source>Файлы и форматы</source>
        <translation>Files and formats</translation>
    </message>
    <message>
        <location filename="../settings_modules/selector_settings_dialog.py" line="133" />
        <location filename="../settings_modules/selector_settings_dialog.py" line="283" />
        <source>Уведомления</source>
        <translation>Notifications</translation>
    </message>
    <message>
        <location filename="../settings_modules/selector_settings_dialog.py" line="106" />
        <location filename="../settings_modules/selector_settings_dialog.py" line="280" />
        <source>Лупа</source>
        <translation>Magnifier</translation>
    </message>
    <message>
        <location filename="../settings_modules/selector_settings_dialog.py" line="124" />
        <location filename="../settings_modules/selector_settings_dialog.py" line="282" />
        <source>Голосовая аннотация</source>
        <translation>Voice annotation</translation>
    </message>
    <message>
        <location filename="../settings_modules/selector_settings_dialog.py" line="48" />
        <location filename="../settings_modules/selector_settings_dialog.py" line="274" />
        <source>Настройки выбора элементов</source>
        <translation>Element selection settings</translation>
    </message>
</context>
<context>
    <name>SettingsDialog</name>
    <message>
        <location filename="../voice_control/ui/settings_dialog.py" line="18" />
        <source>Настройки распознавания речи</source>
        <translation>Speech recognition settings</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_dialog.py" line="23" />
        <source>Закрыть</source>
        <translation>Close</translation>
    </message>
</context>
<context>
    <name>SettingsTabRecognizer</name>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="50" />
        <source>Тип распознавателя</source>
        <translation>Recognizer type</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="51" />
        <source>Yandex SpeechKit</source>
        <translation>Yandex SpeechKit</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="53" />
        <source>Локальный (Vosk)</source>
        <translation>Local (Vosk)</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="54" />
        <source>Google Cloud Speech-to-Text</source>
        <translation>Google Cloud Speech-to-Text</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="56" />
        <source>Применить и сохранить настройки</source>
        <translation>Apply and save settings</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="132" />
        <location filename="../voice_control/ui/settings_tab.py" line="136" />
        <location filename="../voice_control/ui/settings_tab.py" line="154" />
        <source>Ошибка</source>
        <translation>Error</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="132" />
        <source>Не найден виджет настроек для {}</source>
        <translation>Settings widget not found for {}</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="136" />
        <source>Виджет настроек для {} не реализует необходимые методы.</source>
        <translation>Settings widget for {} does not implement the required methods.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="154" />
        <source>Неизвестный тип распознавателя: {}</source>
        <translation>Unknown recognizer type: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="159" />
        <source>Успех</source>
        <translation>Success</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="159" />
        <source>Настройки успешно применены и сохранены.</source>
        <translation>Settings have been successfully applied and saved.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="164" />
        <source>Ошибка применения настроек</source>
        <translation>Error applying settings</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tab.py" line="165" />
        <source>Не удалось применить настройки для {}:
{}</source>
        <translation>Failed to apply settings for {}:
{}</translation>
    </message>
</context>
<context>
    <name>SpeechRecognitionWidget</name>
    <message>
        <location filename="../voice_control/ui/main_window.py" line="81" />
        <source>Основные</source>
        <translation>General</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/main_window.py" line="82" />
        <source>Настройки</source>
        <translation>Settings</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/main_window.py" line="83" />
        <source>Распознавание</source>
        <translation>Recognition</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/main_window.py" line="84" />
        <source>Информация</source>
        <translation>Information</translation>
    </message>
</context>
<context>
    <name>SpeechRecognitionWindow</name>
    <message>
        <location filename="../voice_control/ui/main_window.py" line="137" />
        <location filename="../voice_control/ui/main_window.py" line="153" />
        <source>Распознавание речи - Яндекс SpeechKit</source>
        <translation>Speech Recognition - Yandex SpeechKit</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/main_window.py" line="141" />
        <source>Закрыть</source>
        <translation>Close</translation>
    </message>
</context>
<context>
    <name>StatusBar</name>
    <message>
        <location filename="../voice_control/ui/gui_components.py" line="133" />
        <source>Готов</source>
        <translation>Ready</translation>
    </message>
</context>
<context>
    <name>TranslationManager</name>
    <message>
        <location filename="../translation_manager.py" line="194" />
        <source>Select interface language</source>
        <translation>Select interface language</translation>
    </message>
    <message>
        <location filename="../translation_manager.py" line="201" />
        <source>Language</source>
        <translation>Language</translation>
    </message>
</context>
<context>
    <name>UISettingsTab</name>
    <message>
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="40" />
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="159" />
        <source>Настройки выделения</source>
        <translation>Selection settings</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="46" />
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="163" />
        <source>Цвет выделения:</source>
        <translation>Highlight color:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="62" />
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="164" />
        <source>Ширина границы (px):</source>
        <translation>Border width (px):</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="74" />
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="160" />
        <source>Настройки сохранения</source>
        <translation>Save settings</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="80" />
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="165" />
        <source>Каталог автосохранения:</source>
        <translation>Autosave directory:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="83" />
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="168" />
        <source>Обзор...</source>
        <translation>Browse...</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="92" />
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="171" />
        <source>Запоминать последний каталог сохранения</source>
        <translation>Remember last save directory</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="130" />
        <source>Выберите цвет выделения</source>
        <translation>Select highlight color</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/ui_settings_tab.py" line="140" />
        <source>Выберите каталог для автосохранения</source>
        <translation>Select autosave directory</translation>
    </message>
</context>
<context>
    <name>VoiceAnnotationModel</name>
    <message>
        <location filename="../voice_control/voice_annotation_model.py" line="91" />
        <source>VoiceAnnotationModel: Настройки загружены: max_duration={}, auto_rec={}</source>
        <translation>VoiceAnnotationModel: Settings loaded: max_duration={}, auto_rec={}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_model.py" line="82" />
        <source>VoiceAnnotationModel: Менеджер настроек не предоставлен. Используются значения по умолчанию.</source>
        <translation>VoiceAnnotationModel: Settings manager not provided. Default values are used.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_model.py" line="95" />
        <source>VoiceAnnotationModel: Ошибка при загрузке настроек (общая): {}</source>
        <translation>VoiceAnnotationModel: Error loading settings (general): {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_model.py" line="106" />
        <source>VoiceAnnotationModel: Состояние сброшено.</source>
        <translation>VoiceAnnotationModel: State reset.</translation>
    </message>
</context>
<context>
    <name>VoiceAnnotationView</name>
    <message>
        <location filename="../voice_control/voice_annotation_view.py" line="25" />
        <source>Здесь появится распознанный текст...</source>
        <translation>Recognized text will appear here...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_view.py" line="23" />
        <source>Открыть настройки распознавания</source>
        <translation>Open recognition settings</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_view.py" line="24" />
        <source>Завершить аннотацию (Enter)</source>
        <translation>Завершить аннотацию (Enter)</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_view.py" line="170" />
        <source>Resetting VoiceAnnotationView UI.</source>
        <translation>Resetting VoiceAnnotationView UI.</translation>
    </message>
</context>
<context>
    <name>VoiceAnnotationWidget</name>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="166" />
        <location filename="../voice_control/voice_annotation_widget.py" line="458" />
        <source>Распознавание...</source>
        <translation>Recognizing...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="371" />
        <source>audio_capture.stop_recording() не удалось.</source>
        <translation>audio_capture.stop_recording() failed.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="720" />
        <source>Остановка потока распознавания при закрытии виджета...</source>
        <translation>Stopping recognition thread on widget close...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="418" />
        <source>Ошибка обработки аудио: {}</source>
        <translation>Audio processing error: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="508" />
        <source>Очистка ссылок на поток и воркер распознавания.</source>
        <translation>Cleaning up references to recognition thread and worker.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="379" />
        <source>Ошибка при вызове audio_capture.stop_recording: {}</source>
        <translation>Error calling audio_capture.stop_recording: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="555" />
        <source>Ошибка: {}</source>
        <translation>Error: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="334" />
        <source>Повторная загрузка распознавателя не удалась</source>
        <translation>Recognizer reload failed</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="403" />
        <source>Автоматическое распознавание включено, запускаем _recognize_recorded_audio.</source>
        <translation>Automatic recognition enabled, starting _recognize_recorded_audio.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="557" />
        <location filename="../voice_control/voice_annotation_widget.py" line="571" />
        <source>Ошибка распознавания: {}</source>
        <translation>Recognition error: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="821" />
        <source>Cleanup for VoiceAnnotationWidget complete.</source>
        <translation>Cleanup for VoiceAnnotationWidget complete.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="551" />
        <source>Ошибка: не удалось распознать текст.</source>
        <translation>Error: failed to recognize text.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="206" />
        <source>Неизвестный тип распознавателя: {}</source>
        <translation>Unknown recognizer type: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="541" />
        <source>Ошибка при сборке текста из results: {}</source>
        <translation>Error assembling text from results: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="601" />
        <source>Говорите...</source>
        <translation>Speak...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="358" />
        <source>Не удалось начать запись</source>
        <translation>Failed to start recording</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="714" />
        <source>VoiceAnnotationWidget closeEvent</source>
        <translation>VoiceAnnotationWidget closeEvent</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="723" />
        <location filename="../voice_control/voice_annotation_widget.py" line="818" />
        <source>Поток распознавания не завершился штатно, прерываем...</source>
        <translation>Recognition thread did not terminate normally, interrupting...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="554" />
        <source>Неизвестная ошибка распознавания</source>
        <translation>Unknown recognition error</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="783" />
        <source>Сброс и скрытие виджета.</source>
        <translation>Resetting and hiding widget.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="191" />
        <source>Начинаем загрузку распознавателя речи...</source>
        <translation>Starting speech recognizer loading...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="337" />
        <source>Распознаватель успешно загружен при повторной попытке</source>
        <translation>Recognizer successfully loaded on retry</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="704" />
        <source>Нажата клавиша Escape, скрываем виджет без отправки аннотации.</source>
        <translation>Escape key pressed, hiding widget without sending annotation.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="147" />
        <source>Модель: is_recording изменился на {}</source>
        <translation>Model: is_recording changed to {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="323" />
        <source>Возможные причины:</source>
        <translation>Possible reasons:</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="464" />
        <source>Преобразовано в формат кортежа: {} байт, {} Гц, {} канал(ов), {} байт/сэмпл</source>
        <translation>Converted to tuple format: {} bytes, {} Hz, {} channel(s), {} bytes/sample</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="364" />
        <source>Попытка остановить запись...</source>
        <translation>Attempting to stop recording...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="374" />
        <source>Запись не была активна, вызов stop_recording проигнорирован для audio_capture.</source>
        <translation>Recording was not active, stop_recording call ignored for audio_capture.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="750" />
        <source>VoiceAnnotationWidget потерял фокус (reason: {}), но находится в контексте настроек - не скрываем.</source>
        <translation>VoiceAnnotationWidget lost focus (reason: {}), but is in settings context - not hiding.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="360" />
        <source>Ошибка при запуске записи: {}</source>
        <translation>Error starting recording: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="693" />
        <location filename="../voice_control/voice_annotation_widget.py" line="802" />
        <source>VoiceAnnotationWidget reset, hidden, and keyboard released.</source>
        <translation>VoiceAnnotationWidget reset, hidden, and keyboard released.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="685" />
        <location filename="../voice_control/voice_annotation_widget.py" line="793" />
        <source>Attempting to set focus to top level window: {}</source>
        <translation>Attempting to set focus to top level window: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="775" />
        <source>VoiceAnnotationWidget находится в контексте настроек по имени объекта: {}</source>
        <translation>VoiceAnnotationWidget is in settings context by object name: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="633" />
        <source>Завершение аннотации...</source>
        <translation>Finalizing annotation...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="635" />
        <source>Запись активна. Устанавливаем флаг для завершения после распознавания.</source>
        <translation>Recording is active. Setting flag to finalize after recognition.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="286" />
        <source>Google распознаватель создан (язык: {})</source>
        <translation>Google recognizer created (language: {})</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="196" />
        <source>Выбранный тип распознавателя: {}</source>
        <translation>Selected recognizer type: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="690" />
        <location filename="../voice_control/voice_annotation_widget.py" line="799" />
        <source>Fallback: Attempting to set focus to parent: {}</source>
        <translation>Fallback: Attempting to set focus to parent: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="350" />
        <source>Не найдены микрофоны</source>
        <translation>No microphones found</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="322" />
        <source>Не настроен распознаватель речи</source>
        <translation>Speech recognizer not configured</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="576" />
        <source>Ошибка распознавания, скрываем виджет.</source>
        <translation>Recognition error, hiding widget.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="475" />
        <source>Ошибка: неверный формат аудио.</source>
        <translation>Error: invalid audio format.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="416" />
        <source>&lt;нет записи&gt;</source>
        <translation>&lt;no recording&gt;</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="561" />
        <source>Распознавание завершено, скрываем виджет.</source>
        <translation>Recognition complete, hiding widget.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="473" />
        <source>Неподдерживаемый формат аудиоданных: {}</source>
        <translation>Unsupported audio data format: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="806" />
        <source>Starting cleanup for VoiceAnnotationWidget...</source>
        <translation>Starting cleanup for VoiceAnnotationWidget...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="495" />
        <source>Внутренняя ошибка: {}</source>
        <translation>Internal error: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="273" />
        <source>Vosk распознаватель создан (модель: {}, язык: {}, частота: {})</source>
        <translation>Vosk recognizer created (model: {}, language: {}, frequency: {})</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="209" />
        <source>Ошибка при загрузке распознавателя {}: {}</source>
        <translation>Error loading recognizer {}: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="390" />
        <source>UI кнопки и анимация обновлены после остановки записи.</source>
        <translation>Button UI and animation updated after stopping recording.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="815" />
        <source>Остановка потока распознавания...</source>
        <translation>Stopping recognition thread...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="417" />
        <source>Ошибка при обработке аудиоданных в _on_recording_stopped: {}</source>
        <translation>Error during audio data processing in _on_recording_stopped: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="326" />
        <source>3. Проблемы с сетевым подключением к Yandex</source>
        <translation>3. Issues with network connection to Yandex</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="647" />
        <source>Аннотация уже была отправлена один раз, повторная отправка отменена.</source>
        <translation>Annotation has already been sent once, re-sending cancelled.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="657" />
        <source>Аннотация готова: '{}...' ({} символов), режим: {}</source>
        <translation>Annotation ready: '{}...' ({} characters), mode: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="747" />
        <source>VoiceAnnotationWidget потерял фокус (reason: {}), новый фокус: {}, скрываем.</source>
        <translation>VoiceAnnotationWidget lost focus (reason: {}), new focus: {}, hiding.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="622" />
        <source>Настройки распознавания применены из диалога.</source>
        <translation>Recognition settings applied from dialog.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="406" />
        <source>Автоматическое распознавание выключено.</source>
        <translation>Automatic recognition disabled.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="251" />
        <source>Yandex распознаватель создан (язык: {}, модель: {})</source>
        <translation>Yandex recognizer created (language: {}, model: {})</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="413" />
        <source>Не удалось получить аудиоданные из буфера (пустые данные или null).</source>
        <translation>Failed to get audio data from buffer (empty data or null).</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="315" />
        <source>Вызван метод start_recording()</source>
        <translation>start_recording() method called</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="701" />
        <source>Нажата клавиша Enter/Return, завершаем аннотацию.</source>
        <translation>Enter/Return key pressed, finalizing annotation.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="552" />
        <source>Ошибка распознавания: не удалось распознать текст.</source>
        <translation>Recognition error: failed to recognize text.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="325" />
        <source>2. Ошибка при инициализации распознавателя</source>
        <translation>2. Error during recognizer initialization</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="639" />
        <source>Распознавание активно. Устанавливаем флаг для завершения.</source>
        <translation>Recognition is active. Setting flag for completion.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="394" />
        <source>Получен сигнал о завершении записи от audio_capture</source>
        <translation>Received recording completion signal from audio_capture</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="539" />
        <source>Собранный текст из results: {}</source>
        <translation>Assembled text from results: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="400" />
        <source>Аудиоданные успешно получены из буфера: {} байт.</source>
        <translation>Audio data successfully received from buffer: {} bytes.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="330" />
        <source>Попытка повторной загрузки распознавателя...</source>
        <translation>Attempting to reload recognizer...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="642" />
        <source>Запись и распознавание неактивны. Немедленное завершение.</source>
        <translation>Recording and recognition inactive. Immediate termination.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="770" />
        <source>VoiceAnnotationWidget находится в контексте настроек: {}</source>
        <translation>VoiceAnnotationWidget is in settings context: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="494" />
        <source>Ошибка при настройке или запуске потока распознавания: {}</source>
        <translation>Error configuring or starting recognition thread: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="142" />
        <source>Текст в View изменен: '{}...'. Обновляем модель.</source>
        <translation>Text in View changed: '{}...'. Updating model.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="158" />
        <source>Модель: is_recognizing изменился на {}</source>
        <translation>Model: is_recognizing changed to {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="167" />
        <source>Модель: error_message изменился на '{}'</source>
        <translation>Model: error_message changed to '{}'</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="183" />
        <source>Перезагрузка распознавателя речи...</source>
        <translation>Reloading speech recognizer...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="220" />
        <source>Для настройки API ключа откройте диалог настроек через кнопку 'Настройки'</source>
        <translation>To configure the API key, open the settings dialog via the 'Settings' button</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="291" />
        <source>Открытие окна настроек распознавания речи...</source>
        <translation>Opening speech recognition settings window...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="302" />
        <source>Окно настроек закрыто, перезагружаем распознаватель...</source>
        <translation>Settings window closed, reloading recognizer...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="327" />
        <source>Решение: откройте настройки и проверьте API ключ Yandex SpeechKit</source>
        <translation>Solution: open settings and check Yandex SpeechKit API key</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="356" />
        <source>Начата запись звука (макс. длительность: {} сек)</source>
        <translation>Audio recording started (max duration: {} sec)</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="411" />
        <source>Запись завершена. Отредактируйте текст или нажмите 'Готово'.</source>
        <translation>Recording finished. Edit the text or press 'Done'.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="530" />
        <source>Основной текст не найден, пытаемся собрать из 'results'...</source>
        <translation>Main text not found, trying to assemble from 'results'...</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="548" />
        <source>Распознанный текст: '{}...' ({} символов)</source>
        <translation>Recognized text: '{}...' ({} characters)</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="566" />
        <source>Ошибка в потоке распознавания: {}</source>
        <translation>Error in recognition thread: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="318" />
        <source>VoiceAnnotationWidget.start_recording: Попытка начать запись, когда она уже идет. Игнорируется.</source>
        <translation>VoiceAnnotationWidget.start_recording: Attempt to start recording when already active. Ignored.</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="324" />
        <source>1. API ключ Yandex SpeechKit не установлен</source>
        <translation>1. Yandex SpeechKit API key not set</translation>
    </message>
    <message>
        <location filename="../voice_control/voice_annotation_widget.py" line="514" />
        <source>Получен результат распознавания из потока: {}</source>
        <translation>Received recognition result from thread: {}</translation>
    </message>
</context>
<context>
    <name>VoiceSettingsTab</name>
    <message>
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="31" />
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="125" />
        <source>Настройки записи</source>
        <translation>Recording settings</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="37" />
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="129" />
        <source>Максимальная длительность (секунд):</source>
        <translation>Maximum duration (seconds):</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="47" />
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="130" />
        <source>Качество записи:</source>
        <translation>Recording quality:</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="49" />
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="135" />
        <source>Низкое</source>
        <translation>Low</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="49" />
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="135" />
        <source>Среднее</source>
        <translation>Medium</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="49" />
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="135" />
        <source>Высокое</source>
        <translation>High</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="57" />
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="126" />
        <source>Распознавание речи</source>
        <translation>Speech Recognition</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="64" />
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="139" />
        <source>Автоматическое распознавание</source>
        <translation>Automatic recognition</translation>
    </message>
    <message>
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="65" />
        <location filename="../settings_modules/tabs/voice_settings_tab.py" line="140" />
        <source>Отложенное распознавание</source>
        <translation>Delayed recognition</translation>
    </message>
</context>
<context>
    <name>VoskSettingsTab</name>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="32" />
        <source>Настройки Vosk</source>
        <translation>Vosk Settings</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="33" />
        <source>Укажите путь к модели Vosk</source>
        <translation>Specify Vosk model path</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="34" />
        <source>Обзор...</source>
        <translation>Browse...</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="39" />
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="73" />
        <source>Путь к модели:</source>
        <translation>Model path:</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="40" />
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="76" />
        <source>Выберите модель для скачивания:</source>
        <translation>Select model to download:</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="41" />
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="85" />
        <source>Прогресс скачивания:</source>
        <translation>Download progress:</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="42" />
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="88" />
        <source>Язык (если модель указана вручную):</source>
        <translation>Language (if model is set manually):</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="43" />
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="91" />
        <source>Частота дискретизации (Гц):</source>
        <translation>Sample rate (Hz):</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="45" />
        <source>Выберите модель из списка доступных для скачивания.</source>
        <translation>Select a model from the list available for download.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="46" />
        <source>Скачать выбранную модель</source>
        <translation>Download selected model</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="48" />
        <source>Язык обычно определяется выбранной моделью. Это поле может быть информационным или для выбора специфичных вариантов, если модель мультиязычная.</source>
        <translation>The language is usually determined by the selected model. This field can be for information or for selecting specific options if the model is multilingual.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="49" />
        <source>Убедитесь, что выбранная частота дискретизации соответствует модели Vosk.</source>
        <translation>Make sure the selected sample rate matches the Vosk model.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="50" />
        <source>Тестировать загрузку модели</source>
        <translation>Test model loading</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="51" />
        <source>Проверить, может ли модель быть загружена в память. Полезно для больших моделей.</source>
        <translation>Check if the model can be loaded into memory. Useful for large models.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="55" />
        <source>Определяется моделью</source>
        <translation>Determined by model</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="56" />
        <source>Русский (если модель русская)</source>
        <translation>Russian (if model is Russian)</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="57" />
        <source>Английский (если модель английская)</source>
        <translation>English (if model is English)</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="133" />
        <source>Выберите папку с моделью Vosk</source>
        <translation>Select Vosk model folder</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="173" />
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="176" />
        <source>Ошибка Vosk</source>
        <translation>Vosk Error</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="173" />
        <source>Укажите путь к модели Vosk.</source>
        <translation>Specify the path to the Vosk model.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="176" />
        <source>Указанный путь к модели Vosk не существует или не является папкой: {}</source>
        <translation>The specified Vosk model path does not exist or is not a folder: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="250" />
        <source>Скачивание модели</source>
        <translation>Downloading model</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="250" />
        <source>Пожалуйста, выберите модель для скачивания.</source>
        <translation>Please select a model to download.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="265" />
        <source>Модель существует</source>
        <translation>Model exists</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="266" />
        <source>Папка с моделью '{}' уже существует. Перекачать?</source>
        <translation>Model folder '{}' already exists. Redownload?</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="276" />
        <source>Ошибка удаления</source>
        <translation>Deletion error</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="276" />
        <source>Не удалось удалить существующую папку модели: {}</source>
        <translation>Failed to delete existing model folder: {}</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="292" />
        <source>Скачивание завершено</source>
        <translation>Download complete</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="292" />
        <source>Модель '{}' успешно скачана и распакована в:
{}</source>
        <translation>Model '{}' successfully downloaded and unpacked to:
{}</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="305" />
        <source>Ошибка скачивания</source>
        <translation>Download error</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="305" />
        <source>Не удалось скачать модель:
{}</source>
        <translation>Failed to download model:
{}</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="311" />
        <source>Ошибка</source>
        <translation>Error</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="311" />
        <source>Укажите путь к модели для тестирования.</source>
        <translation>Specify the path to the model for testing.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="317" />
        <source>Ошибка модели</source>
        <translation>Model error</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="324" />
        <source>Тест успешен</source>
        <translation>Test successful</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="325" />
        <source>Модель '{}' успешно загружена в память!

Модель готова к использованию для распознавания речи.</source>
        <translation>Model '{}' successfully loaded into memory!

Model is ready to be used for speech recognition.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="327" />
        <source>Тест не пройден</source>
        <translation>Test failed</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/vosk_settings_tab.py" line="328" />
        <source>Загрузка модели была отменена или произошла ошибка.</source>
        <translation>Model download was canceled or an error occurred.</translation>
    </message>
</context>
<context>
    <name>YandexKeyValidator</name>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="322" />
        <source>Неверный API ключ (401)</source>
        <translation>Invalid API key (401)</translation>
    </message>
</context>
<context>
    <name>YandexSettingsTab</name>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="26" />
        <source>Настройки Yandex SpeechKit</source>
        <translation>Yandex SpeechKit Settings</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="27" />
        <source>Введите API-ключ Yandex</source>
        <translation>Enter Yandex API key</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="38" />
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="100" />
        <source>API-ключ:</source>
        <translation>API key:</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="42" />
        <source>Язык:</source>
        <translation>Language:</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="46" />
        <source>Модель:</source>
        <translation>Model:</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="50" />
        <source>Формат аудио:</source>
        <translation>Audio format:</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="54" />
        <source>Частота дискретизации (Гц):</source>
        <translation>Sample rate (Hz):</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="57" />
        <source>Русский</source>
        <translation>Russian</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="58" />
        <source>Английский</source>
        <translation>English</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="59" />
        <source>Турецкий</source>
        <translation>Turkish</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="61" />
        <source>По умолчанию (general)</source>
        <translation>Default (general)</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="62" />
        <source>Распознавание коротких фраз (general:rc)</source>
        <translation>Short phrase recognition (general:rc)</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="64" />
        <source>Авто (рекомендуется для OggOpus)</source>
        <translation>Auto (recommended for OggOpus)</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="66" />
        <source>Проверить ключ</source>
        <translation>Check key</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="67" />
        <source>Не проверен</source>
        <translation>Not checked</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="103" />
        <source>Статус ключа:</source>
        <translation>Key status:</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="181" />
        <source>Ошибка Yandex</source>
        <translation>Yandex Error</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="181" />
        <source>Введите API-ключ для Yandex SpeechKit.</source>
        <translation>Enter API key for Yandex SpeechKit.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="218" />
        <source>Проверка ключа Yandex</source>
        <translation>Checking Yandex key</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="218" />
        <source>API-ключ не введен.</source>
        <translation>API key not entered.</translation>
    </message>
    <message>
        <location filename="../voice_control/ui/settings_tabs/yandex_settings_tab.py" line="221" />
        <source>Проверка...</source>
        <translation>Checking...</translation>
    </message>
</context>
</TS>