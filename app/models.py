from dataclasses import dataclass, field
import uuid


@dataclass
class Book:
    title: str
    author: str
    description: str
    status: str
    year_published: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)


db = [
    Book(
        title="1984",
        author="George Orwell",
        description="A dystopian novel",
        status="available",
        year_published=1949,
    )
]
