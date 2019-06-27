# Broadlink Universal IR Remote Controller plugin for Domoticz
Broadlink Universal IR Remote Controller plugin for Domoticz. **Note:** This plugin is under development. This plugin was tested with python 3.5.x and Domoticz 4.x installed on Raspberry Pi.

### Currently supported:
- [x] Broadlink RM2 Pro/Plus
- [x] Broadlink RM mini3

Plugin creates a **control center**. The control center have 5 buttons. `Reset Level` - used to reset incorrectly recognized IR code. `Learn` - used to receive (learn) IR code, `Test` - to test received IR code, `Save Level` - to save received commands into memory. There is another button - `Create`, it creates a new device in Domoticz to control your devices with an IR port.

![control center](https://github.com/Whilser/Broadlink-RM2-Universal-IR-Remote-Controller-Domoticz-plugin/raw/master/images/Command.png)

If before pressing `Create` only one level was saved, creates a Push On button, if two levels was saved it a Switch creates, which allows to turn on and off devices with an IR port. If 3 or more levels was saved, a selector switch is creates.

The plugin supports sending **several IR commands at once** when switching on / off in Domoticz. Just press the `Learn` button several times with sending an IR command from the remote before saving the level (`Save` button).

# Установка / How to Install:

    sudo apt-get install python3 python3-dev python3-pip
    sudo apt-get install libffi-dev libssl-dev
    sudo pip3 install -U pip setuptools
    sudo pip3 install -U virtualenv
    cd domoticz/plugins
    git clone https://github.com/Whilser/Broadlink-RM2-Universal-IR-Remote-Controller-Domoticz-plugin.git BroadlinkIR
    cd BroadlinkIR
    virtualenv -p python3 .env
    source .env/bin/activate
    sudo pip3 install broadlink==0.10
    deactivate

    sudo service domoticz restart

Units Example:

![control center](https://github.com/Whilser/Broadlink-RM2-Universal-IR-Remote-Controller-Domoticz-plugin/raw/master/images/Units.png)

# Плагин Broadlink Universal IR Remote Controller для Domoticz

Внимание! Плагин находится в разработке, в дальнейшем возможны изменения в работе плагина.

### Поддерживаемые устройства:
- [x] Broadlink RM2 Pro/Plus
- [x] Broadlink RM mini3

Для настройки плагина заходим в панель управления Domoticz **Настройки** -> **Оборудование** из выпадающего списка выбираем Broadlink Universal IR Remote Controller, даем ему имя, например, Broadlink, вводим mac адрес устройства. Флажок `Debug` предназначен для выявления ошибок и отладки плагина. Для того, чтобы техническая информация не сыпалась в консоль, флажок `Debug` рекомандуется установить в положение `False`. Нажимаем **Добавить**, после этого в переключателях появится командный центр управления Broadlink Universal IR Remote Controller.

Центр управления имеет несколько кнопок. `Reset Level` - используется для сброса неправильно распознанных команд с физических пультов при обучении. `Learn` - используется для получения (обучения) пульта Broadlink, `Test` - для тестирования полученных ИК команд, `Save Level` - для сохранения этих команд в память. Есть еще одна кнопка - `Create`, она создает новое устройство в Domoticz для управления устройствами с ИК портом.

Если до нажатия `Create` был сохранен один уровень команд, создается кнопка (Push On button), если два - обычный выключатель (Switch), позволяющий включать и выключать устройства с ИК портом. Если уровней 3 и более - создается селекторный переключатель.

Созданные устройства можно редактировать, меняя значок, имя и название уровней.

# Как добавить кнопку
Нажимаем `Reset Level`  -> `Learn` после того, как индикатор на  Broadlink Universal IR Remote Controller замигал, направляем на него пульт и нажимаем кнопку, которую хотим добавить. После этого нажимаем `Test` и если все прошло хорошо и команда сработала - нажимаем `Save Level` -> `Create`

# Как добавить выключатель
Нажимаем `Reset Level`  -> `Learn` после того, как индикатор на  Broadlink Universal IR Remote Controller замигал, направляем на него пульт и нажимаем кнопку, которую хотим добавить на включение, после этого нажимаем `Test` и если все прошло успешно, команда сработала - нажимаем `Save Level`. Для захвата следующей команды нажимаем `Learn` после того, как индикатор на  Broadlink Universal IR Remote Controller замигал, нажимаем кнопку, которую хотим добавить на выключение, далее нажимаем `Test`. Если команда корректно сработала, нажимаем `Save Level`. Если по каким-то причинам команда не распознана, просто нажимаем `Reset Level` и повторяем все сначала. После добавления команды и успешного тестирования, нажимаем `Create` для создания выключателя.

Добавление селекторного выключателя ничем не отличается, кроме того, что процедуру сканирования ИК кода необходимо повторить столько раз, сколько необходимо уровней, нажимая каждый раз после добавления уровня Save Level, по окончании добавления всех команд необходимо нажать `Create`.

# Как добавить сразу несколько ИК команд на включение
Плагин поддерживает отправку **сразу несколько ИК команд** при включении/выключении/переключении. Это может быть полезно, например, для переключения каналов на ТВ при цифровом наборе (либо для устройств, для выключения режима на которых необходимо нажать на несколько кнопок). Рассмотрим добавление на примере кнопки.

Допустим, нам необходимо переключить на канал с номером 916. Нажимаем `Reset Level` -> Learn нажимаем на пульте кнопку  9   -> `Learn` нажимаем на пульте кнопку 1 -> `Learn` нажимаем на пульте кнопку 6. Далее нажимаем `Test`. На этом этапе пульт отправит сразу три команды "916". В случае успеха нажимаем `Save Level` -> `Create`. Все! Кнопка включения канала с номером 916 создана и готова к использованию в сценариях автоматизации системы Domoticz. Аналогичным способом создаются выключатели и селекторные переключатели.

Если устройства надоели и больше не хотите далее использовать, можно их удалить. Для этого заходим настройки - устройства. Слева ставим галочку Chuangmi (для отображения только устройств плагина), далее напротив устройства, которое мы хотим удалить нажимаем на стрелочку.

Просто удалять устройства из переключателей бесполезно, они там снова воссоздаются после перезагрузки системы плагинов.
