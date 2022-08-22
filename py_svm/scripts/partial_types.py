from queue import Empty
from prisma.models import ModuleMeta, Module


ModuleMeta.create_partial(
    "MetadataWithoutRelations",
    optional={"id"},
    exclude_relational_fields=True,
)
