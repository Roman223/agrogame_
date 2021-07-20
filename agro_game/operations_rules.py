import numpy as np


class Rule:
    def __init__(self, essence, durations, culture):
        self.essence = essence
        self.durations = durations
        self.culture = culture

    def __repr__(self):
        return f"{self.culture}"


class ProductivityRule(Rule):
    def __init__(self, essence, durations, culture):
        super().__init__(essence, durations, culture)
        self.productivity_matrix = None

    @staticmethod
    def get_productivity_matrix(num_actions: int, difficulty):
        productivity_matrix = np.identity(num_actions)

        for i in range(productivity_matrix.shape[0]):
            for j in range(productivity_matrix.shape[0]):
                if i == j:
                    continue
                # elif i > j:
                #     if i - j == 1 or i - j == 2:
                #         productivity_matrix[i][j] = .5
                #     continue
                else:
                    step = round(difficulty / (productivity_matrix.shape[0] - i), 2)

                    if productivity_matrix[i][j - 1] - step > 0:
                        productivity_matrix[i][j] = productivity_matrix[i][j - 1] - step
                    else:
                        productivity_matrix[i][j] = 0

        return productivity_matrix

    def set_productivity(self, number_of_operations, difficulty=1.2):
        self.productivity_matrix = self.get_productivity_matrix(number_of_operations, difficulty)

    @staticmethod
    def get_datecode(current_time, essence):
        for code, limits in essence.items():
            if limits[0] == current_time.month and (limits[1] <= current_time.day <= limits[2]):
                return code

    def apply_rule(self, current_time, operation_index):
        datecode = self.get_datecode(current_time=current_time, essence=self.essence)
        if datecode is not None:
            return round((self.productivity_matrix[datecode][operation_index]) * 100, 3)
        else:
            return 0

# from agro_game.rules_config import *
# rule = ProductivityRule(YP_rule, YP_duration, 'Test')
# print(rule.get_productivity_matrix(10, 1).round(3), '\n')