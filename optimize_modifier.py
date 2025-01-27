from ovito.pipeline import ModifierInterface
from ovito.data import DataCollection
import numpy as np

from energy import total_energy

# ModifierInterface — это интерфейс в библиотеке OVITO, который используется для создания пользовательских модификаторов
# (модифицирующих операций) в конвейере обработки данных (data pipeline). Эти модификаторы применяются к данным,
# проходящим через конвейер OVITO, и позволяют пользователю настраивать и автоматизировать обработку данных.
#
# Pipeline принимает в себя все, что "похоже" на ModifierInterface. В данном случае мы наследуемся от него и переписываем
# метод modify под нашу логику. Это позволило задать поведение пайплайна здесь один раз, далее этот модификатор будет
# вызываться автоматически для каждого кадра анимации библиотекой OVITO
#
# Основные особенности ModifierInterface:
# Программируемые модификаторы: Пользователь может определять свои собственные модификаторы, которые будут выполняться на
# данных OVITO, например, добавлять пользовательские вычисления или изменять атрибуты атомов, связей и других элементов.
#
# Метод modify(frame, data): Ключевой метод интерфейса, который вызывается OVITO для применения модификатора к данным.
#
# frame: Индекс текущего кадра анимации или данных.
# data: Объект DataCollection, представляющий набор данных для обработки. Пользователь пишет код, чтобы изменить или
# анализировать данные внутри этого метода.
# Гибкость: ModifierInterface может работать с различными типами данных OVITO, включая:
#
# Позиции атомов,
# Связи (bonds),
# Типы частиц (particle types),
# Свойства данных (data attributes).
# Использование в Python: Пользовательские модификаторы часто реализуются в виде классов, которые наследуют
# ModifierInterface или создаются с использованием функционального интерфейса модификаторов Python.
#
# Наследование в Python — это механизм объектно-ориентированного программирования, который позволяет создавать новый класс (называемый производным или дочерним) на основе уже существующего класса (называемого базовым или родительским). Дочерний класс наследует все атрибуты и методы родительского класса, но также может добавлять новые или переопределять существующие.
#
# Зачем нужно наследование?
# Повторное использование кода: позволяет избежать дублирования кода, если несколько классов имеют общие свойства или поведение.
# Расширение функциональности: можно добавить новые методы или переопределить существующие, чтобы изменить поведение.
# Иерархия и организация: помогает организовать код, представляя отношения между объектами, например, "является" (is-a).
#
# Интерфейс в Python — это абстрактный класс, который определяет набор методов, которые должен реализовать класс, чтобы
# считаться совместимым с этим интерфейсом. Интерфейсы используются для обеспечения контрактного
# поведения: любой класс, реализующий интерфейс, должен содержать все его методы.

class OptimizeModifier(ModifierInterface):
    """
    Класс для оптимизации структуры молекулы через модификацию позиций атомов.
    Используется механизм наследования от ModifierInterface из OVITO.
    """

    # Атрибут для хранения лучших позиций атомов (с минимальной энергией)
    best_positions = None

    # Переопределяем метод под наши нужды
    def modify(self, data: DataCollection, *, frame: int, **kwargs):
        """
        Метод для изменения данных в конвейере OVITO.

        :param data: DataCollection - объект данных, содержащий информацию о частицах, связях и других свойствах.
        :param frame: int - номер текущего кадра (может быть полезным в анимации).
        :param kwargs: dict - дополнительные параметры.
        """
        # Если best_positions еще не инициализирован, сохраняем текущие позиции атомов
        if self.best_positions is None:
            self.best_positions = data.particles_.positions_[:]  # Копируем начальные позиции

        # Вычисляем начальную энергию структуры
        initial_energy = total_energy(data)

        # Количество атомов в системе
        num_atoms = len(data.particles_.positions_)

        # Сохраняем текущие позиции для возможного отката
        initial_positions = self.best_positions[:]

        # Устанавливаем текущие позиции атомов в системе равными лучшим найденным
        for i in range(num_atoms):
            data.particles_.positions_[i] = self.best_positions[i]

        # Параметры случайного сдвига атомов
        max_shift = 0.05  # Максимальная величина сдвига по каждой координате (в Å)

        # Генерация случайных сдвигов в диапазоне [-max_shift, max_shift]
        random_shifts = np.random.uniform(-max_shift, max_shift, size=(num_atoms, 3))

        # Применяем сдвиги к текущим позициям атомов
        data.particles_.positions_ += random_shifts

        # Также обновляем best_positions для сохранения изменений
        self.best_positions += random_shifts

        # Вычисляем новую энергию после применения сдвигов
        new_energy = total_energy(data)

        # Если новая энергия выше начальной, откатываем изменения
        if initial_energy < new_energy:
            # Возвращаем позиции атомов в их изначальное состояние
            self.best_positions[:] = initial_positions

        # Обновляем текущие позиции атомов в системе, устанавливая лучшие позиции
        data.particles_.positions_ = self.best_positions
