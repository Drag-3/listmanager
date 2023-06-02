from collections import defaultdict


class IDGenerator:
    last_id = defaultdict(int)

    @classmethod
    def generate_id(cls, class_name):
        cls.last_id[class_name] += 1
        return cls.last_id[class_name]

    @classmethod
    def set_id(cls, class_name, value):
        cls.last_id[class_name] = value  # Take care to avoid duplicate IDs

    @classmethod
    def get_id(cls, class_name):
        return cls.last_id[class_name]
