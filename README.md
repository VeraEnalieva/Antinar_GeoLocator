# Геокодирование
## _Список адресов на географическую карту_

Создаёт пространственные точечные объекты из списка адресов. 
Ориентирован в первую очередь на данные проекта "Антинар": таблицы Отравления и Сообщения.

- Требуется ключ от Яндекс.Разработчик
- Установленный QGIS Desktop
- ✨Magic ✨

## Краткое описание

- Step_1_preparation.py обрабатывает исходные табличные данные: устанавлвает id, формирует поле Mesto, делит весь материал на части по 950 строк.
- Результат предыдущего шага необходимо пропустить через *.xlsb таблицу, получить координаты. Сформировать соответствующие файлы *.csv
- Загрузить получившиеся файлы, а так же дополнителольно полигоны зданий EAS, в QGIS
- Step_2_QGIS.py запустить из-под консоли в QGIS. Он собирает все файлы в единый пространственный слой, добавляет поле ID_BUILDING_EAS 
- Проверить результат. Некоторые объекты, которые некорректно привязались, передвинуть на нужные улицы.


> В ядре процедуры лежит сервис геокодирования
> от Яндекс. Он доступен для использования в 
> некомерческих целях всем желающим. Необходима
> регистрация через Яндекс.Кабинет Разработчика.
> В бесплатной версии кабинета доступно геодикоривание
> до 1000 строк в сутки.
> 
> Для привязки кодов ЕАС необходим соответсвующий полигональный
слой пространственных данных с полем ID_BUILDINS_EAS. Актуальную
версию этого слоя можно выгрузить из БД  (---ссылка--). 


Предварительно должно быть:
- [Яндекс](https://yandex.ru/dev/jsapi-v2-1/doc/ru/#get-api-key) - кабинет разработчика. Необходимо получить ключ
- [QGIS](https://www.qgis.org/en/site/forusers/download.html) - актуальная версия. Лучше использовать OSGeo4W Network Installer
- актуальный полигональный слой со зданиями и кодами ЕАС
- актуальный полигональный слой с муниципальными округами


## Пошаговая инструкция:
- Откройте _step_1_preparation.py_ в любом из текстовых редакторов
- В начале файла есть раздел #USER_SETTINGS. Укажите параметры _xls_file_ (папка, где лежат исходные данные) и _type_ (тип исходных данных: отравления или сообщения)
- Запустите скрипт. Рядом с исходными файлом появятся файлы с постфиксом _full и _part*. Full-файл необходимо будет подгрузить в проект QGIS потом. А с файлами part* нужно поработать в xls таблице
- Откройте _GeoYandex.xlsb_  в Excel (к сожалению в OpenOffice он пока не работает). На листе _options_ напротив API Yandex укажите ключ от кабинета
- На вкладке _Адреса_ не меняя заголовок таблицы вставьте данные из _*_part*.csv_ таким образом, чтобы заначения из первой колонки попали в поле _set_id_, а значения из второй колонки попали в поле _adr_src_
- Скопируйте колонку _adr_src_ на вкладку _yandex_ в колонку _Объект для поиска (адрес либо координаты)_
- Нажмите кнопку _Получить координаты_. Через некоторое время заполнятся остальные колонки на этой вкладке
- Скопируйте все данные снова на вкладку _Адреса_. Таким образом у вас получится списовк адресов и с координатами, и с _id_
- Сохраните полученный результат в новый _*.csv_. Название может быть любым. Важно, чтобы оно содержало буквы _*coord*.csv_
- Проделайте аналогичные манипуляции с каждым из *_part*.csv. Помните, что в бесплатной версии можно обрабатывать не более 1000 строк с одного аккаунта в день! В противном случае Яндекс блокирует доступ до конца суток. А в избыточные строки не все привязывает.
- Откройте QGIS Desktop
- Создайте новый или используйте старый проект. Обязательные условия: в проект должен быть подгружен слой с полигональными зданиями от ЕАС. Слой должен называться _building_EAS_. Обращайте внимание на системы координат! 
- Подгрузите в проект текстовые файлы с координатами (_*coord*.csv_) и  _*_full.csv_
- Проверьте каждый файл открыв таблицу атрибутов. Убедитесь, что у них корректные названия полей, названия улиц правильно оторажаются. Если поломалась кодировка. то  в свойстах слоя на вкладке _Свойства->Текст->Настройки->Кодировка_ укажите UTF-8
- Для удобства и наглядности можно подгрузить любые другие данные. Например подложку OSM.
- Из-под QGIS откройте Python консоль. И в ней скрипт _step_2_QGIS.py_
- Укажите в скрипте в #USER_SETTNIG путь к исходному xls. Выполните скрипт (зелёный треугольник _play_)
- Если всё сделано правильно, то у в преокте у вас появится слой c названием, аналогичных исходному xls файлу. Этот файл уже можно экспортировать в любой географический или даже текстовый формат. Нас интересует GML.
- На скриншоте Export2GL отмечены важные пункты настроек экспорта.
- Хорошая практика — проверить результат.

## Проверка результата
- Кодировка текста
- Система координат. Геокодирование от Яндекса - это географические координаты в десятичных градусах (WGS84, EPSG:4326). Большинство внутренних информационных систем - это метрические местные системы координат. Например, МСК-64. Если есть путанница в СК, то данные из разных источников будут "отлетать" или быть не видными в проекте
- Посмотрите точки в Дворцовой площади. Сюда, как в центр города, могу попасть происшествия, для которых адрес был не найден.
- Раскрасьте точки _POINTS_ по полю _District_. Так можно легко увидеть глазами некоторые ошибки привязки, связанные с разночтениями или ошибками исходных данных. Точки можно передвинуть в режиме редактирования на нужные территории.
- Выведите надписями адреса из поля 'Mesto'. Аналогично выведите адреса из других источников данных (например ЕАС), выборочно пройдитель по ним, посмотрите разницу
- Проверьте поличество строк с исходном файле и количество строк в слое точек. Нормальная ситуация, если в точечном слое их немного меньше, чем в исходном. В алгоритме обработки удаляются те строки, для которых никакой адрес не был указан. Разница не должна быть большой.

## Алгоритмы
**_Привязка номера дома_** (в случае если не указано) из ЕАС на основании координат;
Реализовано по следующему алгоритму.
- Если точка на карте попадает в контур здания (геослой БД системы ТОРИС EAS.EAS), то привязывается код EAS;
- Если точке на карте НЕ попадаетв контуре, то ищется ближайшее здание из данных EAS в радиусе 500 метров. При этом в итоговом файле есть атрибут distance. В нем указано расстояние ближайшего найденного.
- Для всех адресов в итоговом файле есть атрибуты с перфиксом EAS: EAS_PADDRESS, EAS_HOUSE, EAS_LITER. Это атрибуты адресов из БД ТОРИС EAS.EAS. Названия полей заимствованы из этой же БД; Эти поля служат для проверки операторов результата привязки. После проверки и перед выгрузкой в итоговый файл все поля после distance включительно следует удалить.

**_Районы города_**
В проект QGIS должен быть загружен слой полигональных объектов "Районы Города". К какому полигону принадлежит точка, тот район и будет указан в поле FACT_RAYON итогового файла. Автозамену не стала реализовывать. Всё  же это нужно просмотреть запросом ("District" <>  "FACT_RAYON") и глазами ввиду вариативности входящих данных. Тем не менее, после проверки оператором, калькулятором полей проверенные значения можно будет посчитать в два клика. Поле  FACT_RAYON  временное, после проверки и перед выгрузкой нужно удалить.

**_Адреса без номера дома_**
На первом этапе обработки (до геолокации): если не указан номер дома, то по умолчанию ему присваивается значение 1 для некрупных улиц и улиц, которых нет в словаре.
Словарь представляет собой текстовый файл street_dict_file.txt, где перечислены улицы, для которых недостаточно указывать единицу. Для них необходимо анализировать район города. И в зависимости от района присваивается номер дома по словарю. Словарь вынесен во внешний файл, чтобы была возможность редактирования пользователем.
По результатам исследования при таком алгоритме и итоговая геолокация и позиционирование точек на карте значительно лучше, чем при геолокации со значениями Nan. Тем не менее, при таком подходе ошибки позиционирования всё равно остаются. Статистика такая:
из около 1500 объектов, 76 не содержат номеров домов в исходниках. Их необходимо просматривать глазами. Из них около 10 привяжутся неверно.
В итоговом файле в поле HouseNum остаётся такое значение, которое было в исходных данных, в том числе Nan, в поле adr_src появляется единица.



## Полезности
> Для того, чтобы на карте подписи в QGIS не были такими длинными и не выводили наименование города,
> в свойствах надписей указать выражение  _string_to_array("adr_src", 'Санкт-Петерубрг,')[1]_
>
