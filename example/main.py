from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal, Optional

import structutils


type Locale = Literal['en', 'fr']
type Localized[T] = dict[Locale, T]

type LocalizedText = Localized[str]

@dataclass
class EstablishmentObject:
    age: int
    """The age of the establishment in years."""

    name: Optional[LocalizedText] = None

# print(
#     instantiate(EstablishmentObject, {
#         # 'name': { 'en': 'The Great Restaurant', },
#     }),
# )
# # print(instantiate(Locale, 'en'))

with Path('example/schema.json').open('w') as file:
    json.dump(structutils.generate(EstablishmentObject), file, indent=4)
