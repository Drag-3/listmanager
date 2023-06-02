from dataclasses import dataclass, fields
from taskmn.conv import IDGenerator


@dataclass
class Tag:
    name: str
    _id: int = 0

    def __post_init__(self):
        self._id = IDGenerator.generate_id(self.__class__)

    @property
    def id(self):
        return self._id

    @classmethod
    def load_from_data(cls, tag_id: int, tag_name: str):
        tag = Tag(tag_name)
        tag._id = tag_id
        IDGenerator.set_id(cls.__class__, IDGenerator.get_id(cls.__class__) - 1)
        return tag

    def to_list(self):
        return [str(self.id), str(self.name)]


if __name__ == "__main__":
    tags = []
    for i in range(15):
        tags.append(Tag(i))

    print(tags)
